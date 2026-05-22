"""
向量层（Vector Layer）- Phase 2

基于语义向量的Session相似度判定

PRD V7.5 §会话切割：
- sim > 0.40 → CONTINUE（同一主题延续）
- sim < 0.15 → CUT（主题切换）
- 0.15-0.40 → 模糊地带，看历史趋势
  - 趋势均值 > 0.25 → CONTINUE
  - 否则 → PENDING（进入LLM层）
"""

from typing import List, Optional, Tuple
from enum import Enum
import math


class VectorDecision(Enum):
    CONTINUE = "continue"
    CUT = "cut"
    PENDING = "pending"


class VectorLayer:
    """向量层 - Phase 2"""

    THRESHOLD_HIGH = 0.40
    THRESHOLD_LOW = 0.15
    TREND_WINDOW = 5
    TREND_THRESHOLD = 0.25

    def __init__(self, embedder=None, preprocessor=None, chroma_collection=None):
        from .preprocessor import TurnPreprocessor
        self._embedder = embedder
        self._preprocessor = preprocessor or TurnPreprocessor()
        self._chroma_collection = chroma_collection
        self._session_vectors: List[List[float]] = []
        self._similarity_history: List[float] = []

    def set_chroma_collection(self, collection):
        """设置ChromaDB集合"""
        self._chroma_collection = collection

    def set_embedder(self, embedder):
        self._embedder = embedder

    def set_preprocessor(self, preprocessor):
        self._preprocessor = preprocessor

    def reset(self):
        self._session_vectors = []
        self._similarity_history = []

    def _preprocess_content(self, content: str) -> str:
        """预处理内容，返回用于向量嵌入的清洗文本"""
        if self._preprocessor is None:
            return content
        result = self._preprocessor.preprocess(content)
        return result.get("embedding_text", content)

    def add_turn(self, content: str) -> Optional[List[float]]:
        """添加Turn到历史，使用预处理后的文本做向量嵌入"""
        if self._embedder is None:
            return None
        embedding_text = self._preprocess_content(content)
        vector = self._embedder.encode(embedding_text)
        if vector:
            self._session_vectors.append(vector)
        return vector

    def add_message(self, message_id: str, content: str) -> dict:
        """
        添加消息到向量存储，返回预处理结果供上层存入SQLite

        Args:
            message_id: 消息ID
            content: 消息原文

        Returns:
            processed: 预处理结果字典，包含:
                - original: 原文
                - embedding_text: 清洗后文本
                - has_code: 是否包含代码
                - code_hashes: 代码块MD5哈希列表
                - quote_hashes: 引用块哈希列表
                - list_hashes: 列表块哈希列表
                - user_notes: 用户原创注释
        """
        processed = self._preprocessor.preprocess(content)
        embedding_text = processed.get("embedding_text", content)

        if self._embedder is not None:
            vector = self._embedder.encode(embedding_text)
            if vector:
                self._session_vectors.append(vector)

                if self._chroma_collection is not None:
                    self._chroma_collection.add(
                        documents=[embedding_text],
                        embeddings=[vector],
                        metadatas=[{
                            "original_length": len(processed.get("original", "")),
                            "has_code": processed.get("has_code", False),
                            "code_hashes": ",".join(processed.get("code_hashes", [])),
                            "has_quote": len(processed.get("quote_hashes", [])) > 0,
                            "quote_hashes": ",".join(processed.get("quote_hashes", [])),
                            "list_hashes": ",".join(processed.get("list_hashes", [])),
                        }],
                        ids=[message_id]
                    )

        return processed

    def compute_similarity(self, vec1, vec2) -> float:
        """计算余弦相似度"""
        if vec1 is None or vec2 is None:
            return 0.0
        try:
            vec1_len = len(vec1)
            vec2_len = len(vec2)
        except TypeError:
            return 0.0
        if vec1_len == 0 or vec2_len == 0 or vec1_len != vec2_len:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def get_session_average_vector(self) -> Optional[List[float]]:
        if not self._session_vectors:
            return None
        dim = len(self._session_vectors[0])
        avg = [0.0] * dim
        for v in self._session_vectors:
            for i, val in enumerate(v):
                avg[i] += val
        for i in range(dim):
            avg[i] /= len(self._session_vectors)
        return avg

    def decide(
        self,
        current_turn_content: str,
        current_turn_vector: Optional[List[float]] = None,
        previous_turn_content: Optional[str] = None
    ) -> Tuple[VectorDecision, str, dict]:
        """向量层判定，使用预处理后的文本"""

        if self._embedder is None:
            return VectorDecision.CONTINUE, "无嵌入模型，默认延续", {}

        embedding_text = self._preprocess_content(current_turn_content)

        if current_turn_vector is None:
            current_turn_vector = self._embedder.encode(embedding_text)
            if current_turn_vector is None:
                return VectorDecision.CONTINUE, "嵌入失败，默认延续", {"error": "embedding_failed"}

        if current_turn_vector is None or (hasattr(current_turn_vector, '__len__') and len(current_turn_vector) == 0):
            return VectorDecision.CONTINUE, "嵌入为空，默认延续", {}

        if not self._session_vectors:
            return VectorDecision.CONTINUE, "首个Turn，默认延续", {"is_first_turn": True}

        session_avg = self.get_session_average_vector()
        if session_avg is None:
            return VectorDecision.CONTINUE, "无历史向量，默认延续", {}

        similarity = self.compute_similarity(current_turn_vector, session_avg)
        self._similarity_history.append(similarity)

        metadata = {
            "similarity": similarity,
            "similarity_count": len(self._similarity_history),
            "embedding_text": embedding_text[:100]
        }

        if similarity > self.THRESHOLD_HIGH:
            return (
                VectorDecision.CONTINUE,
                f"高相似度（{similarity:.2f} > {self.THRESHOLD_HIGH}）",
                metadata
            )

        if similarity < self.THRESHOLD_LOW:
            return (
                VectorDecision.CUT,
                f"低相似度（{similarity:.2f} < {self.THRESHOLD_LOW}）",
                metadata
            )

        trend_avg = self._get_trend_average()
        if trend_avg is not None and trend_avg > self.TREND_THRESHOLD:
            return (
                VectorDecision.CONTINUE,
                f"历史趋势延续（均值{trend_avg:.2f} > {self.TREND_THRESHOLD}）",
                {**metadata, "trend_avg": trend_avg}
            )

        return (
            VectorDecision.PENDING,
            f"模糊地带（{similarity:.2f}），趋势不足",
            {**metadata, "trend_avg": trend_avg}
        )

    def _get_trend_average(self) -> Optional[float]:
        if len(self._similarity_history) < 2:
            return None
        recent = self._similarity_history[-self.TREND_WINDOW:]
        if not recent:
            return None
        return sum(recent) / len(recent)

    def get_stats(self) -> dict:
        return {
            "turn_count": len(self._session_vectors),
            "similarity_count": len(self._similarity_history),
            "last_similarity": self._similarity_history[-1] if self._similarity_history else None,
            "trend_average": self._get_trend_average()
        }
