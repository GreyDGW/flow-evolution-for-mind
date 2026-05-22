"""
LLM 精判层（第三层）
触发条件：向量层模糊地带 + (Session >= 10 Turn 或情绪硬信号)
输出协议：放弃 JSON，改用文本模糊匹配（继续 / 切割 / 切割-摆烂）
"""

from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class LLMArbiter:
    """LLM 精判器"""

    PROMPT_TEMPLATE = """你是一名对话分析师。请判定以下新消息是否应该开启新会话。

当前会话主题历史：{topic_tags}
新消息：{content}
与历史相似度：{similarity:.2f}（0.25-0.55 为模糊地带）

判定规则：
- 同一主题的深入/追问/补充 → 回复"继续"
- 明显切换到无关主题 → 回复"切割"
- 短暂中断后回到原主题 → 回复"继续"
- 情绪宣泄/闲聊且与主题无关 → 回复"切割-摆烂"

请只回复一个词：继续 / 切割 / 切割-摆烂。不要解释。"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def arbitrate(self, current_content: str, topic_tags: List[str], similarity: float) -> Tuple[str, str, bool]:
        """返回 (action, reason, is_slump_candidate)"""
        content_snippet = (current_content or "")[:200]
        tags_str = " → ".join(topic_tags) if topic_tags else "（无历史标签）"

        prompt = self.PROMPT_TEMPLATE.format(
            topic_tags=tags_str,
            content=content_snippet,
            similarity=similarity
        )

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            raw_text = response.get("content", "").strip() if isinstance(response, dict) else str(response).strip()
        except Exception as e:
            logger.warning(f"LLM 精判调用失败: {e}")
            return "continue", "LLM调用失败，保守延续", False

        return self._parse_response(raw_text)

    def _parse_response(self, text: str) -> Tuple[str, str, bool]:
        text_lower = text.lower().strip()

        if "切割-摆烂" in text or "摆烂" in text or "slump" in text_lower:
            return "cut", "情绪宣泄/闲聊，标记摆烂候选", True

        if "切割" in text or "cut" in text_lower:
            return "cut", "明显切换到无关主题", False

        if "继续" in text or "continue" in text_lower or not text:
            return "continue", "同一主题深入或回归", False

        logger.warning(f"LLM 精判返回无法识别: '{text}'，降级为延续")
        return "continue", "返回不明确，保守延续", False