"""
会话切割器 - 三层渐进式会话切割

基于 Flow Ecosystem PRD V7.5 §会话切割

三层架构：
- Phase 1: 硬规则层（0ms，80%触发）
- Phase 2: 向量层（<50ms，17%触发）
- Phase 3: LLM精判层（<2s，<3%触发）

嵌入器：ChromaEmbedder（384维 ONNX）
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from enum import Enum
import math

from .embedding import create_embedder, ChromaEmbedder, KeywordEmbedder


class CutDecision(Enum):
    """切割决策"""
    CUT = "cut"       # 切割会话
    CONTINUE = "continue"  # 延续会话
    PENDING = "pending"   # 待判定


class SessionCutResult:
    """切割结果"""

    def __init__(
        self,
        decision: CutDecision,
        reason: str,
        layer: str,
        topic_tag: Optional[str] = None,
        new_topic_tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.decision = decision
        self.reason = reason
        self.layer = layer
        self.topic_tag = topic_tag
        self.new_topic_tag = new_topic_tag
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "action": self.decision.value,
            "reason": self.reason,
            "layer": self.layer,
            "topic_tag": self.topic_tag,
            "new_topic_tag": self.new_topic_tag,
            **self.metadata
        }


class HardRulesLayer:
    """硬规则层 - Phase 1（0ms，80%触发）"""

    def __init__(self):
        self.timeout_minutes = 15
        self.heartbeat_minutes = 120
        self.short_message_threshold = 10
        self.code_block_window_minutes = 5

        self.short_messages = [
            "等一下", "好的", "明白了", "ok", "嗯", "yes", "yeah", "稍等",
            "等我", "一会儿", "等下", "稍候", "知道了", "好的好的"
        ]

        self.explicit_commands = ["/new", "/clear", "/restart", "/reset"]

    def check(
        self,
        current_turn_content: str,
        previous_turn_time: Optional[datetime],
        current_turn_time: datetime,
        previous_has_code: bool,
        current_has_code: bool
    ) -> Tuple[CutDecision, str, Dict[str, Any]]:
        """硬规则检查，返回切割决策"""

        time_gap_minutes = 0
        if previous_turn_time:
            time_gap_minutes = (current_turn_time - previous_turn_time).total_seconds() / 60

        metadata = {"time_gap_minutes": time_gap_minutes}

        # 规则1: 超时切割（>30分钟无输入）
        if time_gap_minutes > self.timeout_minutes:
            return (
                CutDecision.CUT,
                f"超时切割（{time_gap_minutes:.1f}分钟无输入）",
                {"trigger": "timeout"}
            )

        # 规则2: 显式切割命令
        for cmd in self.explicit_commands:
            if current_turn_content.strip().startswith(cmd):
                return (
                    CutDecision.CUT,
                    f"显式切割命令：{cmd}",
                    {"trigger": "explicit"}
                )

        # 规则3: Heartbeat切割（>2小时无活跃）
        if time_gap_minutes > self.heartbeat_minutes:
            return (
                CutDecision.CUT,
                f"Heartbeat切割（{time_gap_minutes:.1f}分钟无活跃）",
                {"trigger": "heartbeat"}
            )

        # 规则4: 短消息豁免（<10字中断词）
        stripped = current_turn_content.strip()
        if (len(stripped) <= self.short_message_threshold and
            any(sm in stripped for sm in self.short_messages)):
            return (
                CutDecision.CONTINUE,
                f"短消息豁免（{len(stripped)}字中断词）",
                {"trigger": "short_message", "content": stripped}
            )

        # 规则5: 代码块延续（前后轮都有代码且<5分钟）
        if (previous_has_code and current_has_code and
            time_gap_minutes <= self.code_block_window_minutes):
            return (
                CutDecision.CONTINUE,
                f"代码块延续（{time_gap_minutes:.1f}分钟内）",
                {"trigger": "code_block"}
            )

        return CutDecision.PENDING, "无法判定，进入下一层", {}


class VectorLayer:
    """向量层 - Phase 2（<50ms，17%触发）

    使用 ChromaEmbedder（384维 ONNX）计算语义相似度
    """

    THRESHOLD_HIGH = 0.40   # sim > 0.40 → CONTINUE
    THRESHOLD_LOW = 0.15   # sim < 0.15 → CUT
    TREND_WINDOW = 5        # 历史趋势窗口
    TREND_THRESHOLD = 0.25  # 趋势均值 > 0.25 → CONTINUE
    ANOMALY_THRESHOLD = 0.95  # 异常高相似度阈值（短句保险规则）

    _EMOTION_SIGNALS = ["摆烂", "废了", "不想干", "好累", "算了", "毁灭吧"]

    MAX_HISTORY = 10  # 滑动窗口：只保留最近 10 条消息的向量

    def __init__(self, embedder=None, llm_client=None):
        self._embedder = embedder or create_embedder()
        self._llm_client = llm_client
        self._session_vectors: List[List[float]] = []
        self._similarity_history: List[float] = []

    def set_embedder(self, embedder):
        """设置嵌入器"""
        self._embedder = embedder

    def set_llm_client(self, llm_client):
        """设置LLM客户端"""
        self._llm_client = llm_client

    def reset(self):
        """重置历史"""
        self._session_vectors = []
        self._similarity_history = []

    def _has_emotion_signal(self, content: str) -> bool:
        """检查情绪硬信号"""
        if not content:
            return False
        return any(sig in content for sig in self._EMOTION_SIGNALS)

    def add_turn(self, content: str) -> Optional[List[float]]:
        """添加Turn并返回向量"""
        if self._embedder is None:
            return None
        try:
            vector = self._embedder.encode(content)
            if vector is not None and (not hasattr(vector, '__len__') or len(vector) > 0):
                self._session_vectors.append(vector)
                # 滑动窗口：只保留最近 MAX_HISTORY 条
                if len(self._session_vectors) > self.MAX_HISTORY:
                    self._session_vectors.pop(0)
            return vector
        except Exception:
            return None

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
        """获取Session历史平均向量"""
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

    def _get_recent_average(self, n: int = 3) -> Optional[List[float]]:
        """获取最近 n 条消息的平均向量（局部窗口）"""
        if not self._session_vectors:
            return None
        recent = self._session_vectors[-n:]
        if not recent:
            return None
        dim = len(recent[0])
        avg = [0.0] * dim
        for v in recent:
            for i, val in enumerate(v):
                avg[i] += val
        for i in range(dim):
            avg[i] /= len(recent)
        return avg

    def decide(
        self,
        current_turn_content: str,
        current_turn_vector: Optional[List[float]] = None,
        previous_turn_content: Optional[str] = None
    ) -> Tuple[CutDecision, str, dict]:
        """向量层判定"""

        if self._embedder is None:
            return CutDecision.CONTINUE, "无嵌入模型，默认延续", {}

        if current_turn_vector is None:
            try:
                current_turn_vector = self._embedder.encode(current_turn_content)
            except Exception:
                return CutDecision.CONTINUE, "嵌入失败，默认延续", {"error": "embedding_failed"}

        if current_turn_vector is None or (hasattr(current_turn_vector, '__len__') and len(current_turn_vector) == 0):
            return CutDecision.CONTINUE, "嵌入为空，默认延续", {}

        if not self._session_vectors:
            return CutDecision.CONTINUE, "首个Turn，默认延续", {"is_first_turn": True}

        # 方案 B：加权混合相似度
        # 0.6 * 最近3条平均（局部整体） + 0.4 * 上一条（相邻变化）
        recent_avg = self._get_recent_average(3)
        if recent_avg is None:
            return CutDecision.CONTINUE, "无历史向量，默认延续", {}

        sim_recent = self.compute_similarity(current_turn_vector, recent_avg)

        if self._session_vectors:
            prev_vector = self._session_vectors[-1]
            sim_prev = self.compute_similarity(current_turn_vector, prev_vector)
        else:
            sim_prev = sim_recent  # 无历史时 fallback

        similarity = 0.6 * sim_recent + 0.4 * sim_prev
        self._similarity_history.append(similarity)

        metadata = {
            "similarity": similarity,
            "similarity_count": len(self._similarity_history)
        }

        # 保险规则：异常高相似度 + 短句 → PENDING（触发LLM仲裁）
        if (similarity > self.ANOMALY_THRESHOLD and
            len(current_turn_content) < 15 and
            (previous_turn_content is None or len(previous_turn_content) < 15)):
            return (
                CutDecision.PENDING,
                f"异常高相似度短句（{similarity:.2f} > {self.ANOMALY_THRESHOLD}），疑似模型Bug，触发LLM仲裁",
                {**metadata, "anomaly_detected": True}
            )

        # sim > 0.65 → CONTINUE
        if similarity > self.THRESHOLD_HIGH:
            return (
                CutDecision.CONTINUE,
                f"高相似度（{similarity:.2f} > {self.THRESHOLD_HIGH}）",
                metadata
            )

        # sim < 0.45 → CUT
        if similarity < self.THRESHOLD_LOW:
            return (
                CutDecision.CUT,
                f"低相似度（{similarity:.2f} < {self.THRESHOLD_LOW}）",
                metadata
            )

        # 0.45-0.65 → 看历史趋势
        trend_avg = self._get_trend_average()
        if trend_avg is not None and trend_avg > self.TREND_THRESHOLD:
            return (
                CutDecision.CONTINUE,
                f"历史趋势延续（均值{trend_avg:.2f} > {self.TREND_THRESHOLD}）",
                {**metadata, "trend_avg": trend_avg}
            )

        # 第三层：LLM 精判层
        return self._llm_arbiter_decision(current_turn_content, similarity, metadata)

    def _llm_arbiter_decision(self, current_turn_content: str, similarity: float, metadata: dict) -> Tuple[CutDecision, str, dict]:
        """第三层：LLM 精判层"""
        turn_count = len(self._session_vectors) + 1
        has_emotion = self._has_emotion_signal(current_turn_content)

        if turn_count < 10 and not has_emotion:
            return (
                CutDecision.CONTINUE,
                "LLM层：未达触发条件，保守延续",
                {**metadata, "turn_count": turn_count, "triggered": False}
            )

        if self._llm_client is None:
            return (
                CutDecision.CONTINUE,
                "LLM层：未配置，默认延续",
                {**metadata, "triggered": False, "error": "llm_not_configured"}
            )

        try:
            from .llm_arbiter import LLMArbiter
            arbiter = LLMArbiter(self._llm_client)
            action, reason, is_slump = arbiter.arbitrate(
                current_content=current_turn_content,
                topic_tags=[],
                similarity=similarity
            )

            if action == "cut":
                return (CutDecision.CUT, f"LLM精判：{reason}", {**metadata, "triggered": True, "slump": is_slump})
            else:
                return (CutDecision.CONTINUE, f"LLM精判：{reason}", {**metadata, "triggered": True})

        except Exception as e:
            return (
                CutDecision.CONTINUE,
                f"LLM层异常降级：{str(e)[:30]}",
                {**metadata, "triggered": True, "error": str(e)[:50]}
            )

    def _get_trend_average(self) -> Optional[float]:
        """获取历史趋势均值"""
        if len(self._similarity_history) < 2:
            return None
        recent = self._similarity_history[-self.TREND_WINDOW:]
        if not recent:
            return None
        return sum(recent) / len(recent)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "turn_count": len(self._session_vectors),
            "similarity_count": len(self._similarity_history),
            "last_similarity": self._similarity_history[-1] if self._similarity_history else None,
            "trend_average": self._get_trend_average()
        }


class LLMCache:
    """LLM判定缓存（24小时TTL）"""

    def __init__(self, ttl_hours: int = 24):
        self._cache: Dict[str, Tuple[CutDecision, str, datetime]] = {}
        self.ttl_hours = ttl_hours

    def _make_key(self, similarity: float, topic_tags: str) -> str:
        return f"{similarity:.2f}_{topic_tags}"

    def get(self, similarity: float, topic_tags: str) -> Optional[Tuple[CutDecision, str]]:
        key = self._make_key(similarity, topic_tags)
        if key in self._cache:
            decision, reason, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(hours=self.ttl_hours):
                return decision, reason
            del self._cache[key]
        return None

    def set(self, similarity: float, topic_tags: str, decision: CutDecision, reason: str):
        key = self._make_key(similarity, topic_tags)
        self._cache[key] = (decision, reason, datetime.now())

    def clear(self):
        self._cache = {}


class LLMArbiterLayer:
    """LLM精判层 - Phase 3（<2s，<3%触发）

    仅在模糊地带（0.25-0.55）且Session≥10Turn或情绪信号时触发
    """

    PROMPT_TEMPLATE = """你是一名对话分析师。请判定以下新消息是否应该开启新会话。

当前会话主题历史：{recent_topic_tags}
新消息：{current_turn_content[:200]}
与历史相似度：{similarity:.2f}（0.25-0.55 为模糊地带）

判定规则：
- 同一主题的深入/追问/补充 → continue
- 明显切换到无关主题 → cut
- 短暂中断后回到原主题 → continue
- 情绪宣泄/闲聊且与主题无关 → cut（标记 slump_candidate）

输出 JSON：
{{
  "action": "cut" | "continue",
  "reason": "20字内解释",
  "topic_tag": "当前主题标签",
  "new_topic_tag": "如果cut，新主题标签",
  "slump_candidate": true | false
}}"""

    def __init__(self, llm_client=None):
        self._llm_client = llm_client
        self._cache = LLMCache()

    def set_llm_client(self, llm_client):
        self._llm_client = llm_client

    def clear_cache(self):
        self._cache.clear()

    def decide(
        self,
        current_turn_content: str,
        recent_topic_tags: List[str],
        current_similarity: float,
        session_turn_count: int,
        has_emotion_signal: bool = False
    ) -> Tuple[CutDecision, str, dict]:
        """LLM精判"""

        if self._llm_client is None:
            return CutDecision.CONTINUE, "LLM未配置，默认延续", {}

        cached = self._cache.get(current_similarity, ",".join(recent_topic_tags[-3:]))
        if cached:
            return cached[0], cached[1] + "（缓存）", {"cached": True}

        # 触发条件检查
        if not (current_similarity >= 0.25 and current_similarity <= 0.55):
            return CutDecision.CONTINUE, "不在模糊地带", {"reason": "similarity_out_of_range"}

        if session_turn_count < 10 and not has_emotion_signal:
            return CutDecision.CONTINUE, "未满足触发条件（Session<10Turn且无情绪信号）", {
                "turn_count": session_turn_count,
                "has_emotion_signal": has_emotion_signal
            }

        prompt = self.PROMPT_TEMPLATE.format(
            recent_topic_tags=", ".join(recent_topic_tags[-5:]) or "无",
            current_turn_content=current_turn_content,
            similarity=current_similarity
        )

        try:
            response = self._llm_client.chat(prompt)
            import json
            result = json.loads(response)

            action = CutDecision.CUT if result.get("action") == "cut" else CutDecision.CONTINUE
            reason = result.get("reason", "LLM判定")
            topic_tag = result.get("topic_tag")
            new_topic_tag = result.get("new_topic_tag")

            self._cache.set(current_similarity, ",".join(recent_topic_tags[-3:]), action, reason)

            return action, reason, {
                "topic_tag": topic_tag,
                "new_topic_tag": new_topic_tag,
                "slump_candidate": result.get("slump_candidate", False)
            }
        except Exception as e:
            return CutDecision.CONTINUE, f"LLM调用失败，默认延续: {str(e)}", {"error": str(e)}


class SessionCutter:
    """会话切割器 - 三层渐进式架构

    PRD V7.5 §会话切割
    """

    def __init__(self, llm_client=None, embedder=None):
        self._hard_rules = HardRulesLayer()
        from .embedding import create_embedder
        actual_embedder = embedder or create_embedder()
        self._vector_layer = VectorLayer(embedder=actual_embedder, llm_client=llm_client)
        self._llm_arbiter = LLMArbiterLayer(llm_client)

    def set_llm_client(self, llm_client):
        """设置LLM客户端"""
        self._llm_arbiter.set_llm_client(llm_client)

    def set_embedder(self, embedder):
        """设置嵌入器"""
        self._vector_layer.set_embedder(embedder)

    def reset_session(self):
        """重置Session状态"""
        self._vector_layer.reset()
        self._llm_arbiter.clear_cache()

    def cut_decision(
        self,
        current_turn_content: str,
        current_turn_time: datetime,
        previous_turn_time: Optional[datetime],
        previous_turn_content: Optional[str] = None,
        session_goal: Optional[str] = None,
        session_turn_count: int = 0,
        recent_topic_tags: Optional[List[str]] = None,
        has_emotion_signal: bool = False
    ) -> SessionCutResult:
        """执行三层渐进式切割判定"""

        # Phase 1: 硬规则层
        previous_has_code = self._has_code(previous_turn_content) if previous_turn_content else False
        current_has_code = self._has_code(current_turn_content)

        decision, reason, metadata = self._hard_rules.check(
            current_turn_content=current_turn_content,
            previous_turn_time=previous_turn_time,
            current_turn_time=current_turn_time,
            previous_has_code=previous_has_code,
            current_has_code=current_has_code
        )

        if decision != CutDecision.PENDING:
            return SessionCutResult(decision, reason, "hard_rules", metadata=metadata)

        # Phase 2: 向量层
        if previous_turn_content:
            self._vector_layer.add_turn(previous_turn_content)

        decision, reason, metadata = self._vector_layer.decide(
            current_turn_content=current_turn_content,
            previous_turn_content=previous_turn_content
        )

        if decision != CutDecision.PENDING:
            return SessionCutResult(decision, reason, "vector_layer", metadata=metadata)

        # Phase 3: LLM精判层
        decision, reason, metadata = self._llm_arbiter.decide(
            current_turn_content=current_turn_content,
            recent_topic_tags=recent_topic_tags or [],
            current_similarity=metadata.get("similarity", 0.5),
            session_turn_count=session_turn_count,
            has_emotion_signal=has_emotion_signal
        )

        return SessionCutResult(
            decision,
            reason,
            "llm_arbiter",
            topic_tag=metadata.get("topic_tag"),
            new_topic_tag=metadata.get("new_topic_tag"),
            metadata=metadata
        )

    def _has_code(self, content: Optional[str]) -> bool:
        """检查内容是否包含代码"""
        if not content:
            return False
        code_markers = ["```", "    ", "\t", "def ", "class ", "import ", "function ", "const ", "let "]
        return any(marker in content for marker in code_markers)


class SemanticSessionCutter:
    """基于语义相似度的 Session 自动切分器"""

    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def cut_sessions(self, messages: List[Dict], threshold: float = 0.15) -> List[List[Dict]]:
        """
        自动切分 Session

        1. 粗切：相邻消息相似度 < threshold → 新 Session
        2. 合并：长度 <= 2 的 Session 豁免合并到相邻大 Session
        """
        if not messages:
            return []

        contents = [m.get('content', '') for m in messages]
        embeddings = self.model.encode(contents)

        def cosine(i: int, j: int) -> float:
            a, b = embeddings[i], embeddings[j]
            norm_a = sum(x*x for x in a) ** 0.5
            norm_b = sum(x*x for x in b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(sum(ai*bi for ai, bi in zip(a, b)) / (norm_a * norm_b))

        session_indices = [[0]]
        for i in range(1, len(messages)):
            if cosine(i - 1, i) < threshold:
                session_indices.append([i])
            else:
                session_indices[-1].append(i)

        merged = []
        i = 0
        while i < len(session_indices):
            ids = session_indices[i]

            if len(ids) <= 2 and i == 0 and len(session_indices) > 1:
                session_indices[i + 1] = ids + session_indices[i + 1]
                i += 1
                continue

            if len(ids) <= 2 and 0 < i < len(session_indices) - 1:
                sim_prev = cosine(session_indices[i - 1][-1], ids[0])
                sim_next = cosine(ids[-1], session_indices[i + 1][0])
                if sim_prev >= sim_next:
                    merged[-1].extend(ids)
                else:
                    session_indices[i + 1] = ids + session_indices[i + 1]
                i += 1
                continue

            if len(ids) <= 2 and i == len(session_indices) - 1 and len(session_indices) > 1:
                merged[-1].extend(ids)
                i += 1
                continue

            merged.append(ids)
            i += 1

        return [[messages[idx] for idx in ids] for ids in merged]

    def get_stats(self, sessions: List[List[Dict]]) -> Dict:
        """返回切分统计"""
        return {
            "total_messages": sum(len(s) for s in sessions),
            "session_count": len(sessions),
            "avg_session_length": sum(len(s) for s in sessions) / len(sessions) if sessions else 0,
            "threshold": 0.15
        }
