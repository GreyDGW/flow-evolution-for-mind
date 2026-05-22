"""
SessionAnalyzer：LLM 4维判定 + 证据提取
"""
import re
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class SessionAnalysis:
    goal_alignment: str
    closure_index: str
    flow_depth: str
    cognition_growth: str
    goal_evidence: str
    closure_evidence: str
    flow_evidence: str
    cognition_evidence: str

class SessionAnalyzer:
    PROMPT_TEMPLATE = '''你是认知分析师。阅读以下对话后，从4个维度给出判定（只选高/中/低），每维附证据（最少80字，无上限，句子必须完整）。

证据必须包含：①时间戳 + ②具体行为 + ③关键决策 + ④用户原话1-2句（用引号标注，禁止编造）+ ⑤简短解读
【证据长度——完整原则】
- 无字数上限：根据内容需要，说完为止
- 宁少勿水：重复、加水、系统视角描述，都是"字数通胀"，禁止
- 宁断勿水：无论多少字，必须把句子说完，禁止截断

【聚焦方向——必须保留】
- 目标对齐：方向调整/目标偏离/优先级决策/资源分配
- 闭环指数：可验证产出/交付物/结论/推进状态/卡点
- 心流深度：专注时长/中断情况/沉浸状态/切换成本
- 认知成长：新概念理解/方法论掌握/思维升级/类比迁移

【底线——禁止】
- 禁止纯形容词堆砌（如"很好""明确""顺利"）
- 禁止重复：用户原话引用后，叙述部分不得重复原话内容
- 禁止系统视角：禁止描述"助手响应了什么"，只写用户的行为和决策
- 禁止编造：原文引用必须真实存在
- 原文引用后用自己的话解读，不要重复原话

1. 目标感：对话是否始终围绕一个核心推进？有无明显滑向无关话题？
2. 闭环感：是否有可交付的产出或明确的下一步？讨论是空转还是有结果？
3. 沉浸感：讨论是否连续深入？逻辑链推进了几层？有无频繁跳跃或打断？
4. 成长感：是否产生了新理解或概念连接？有无跨领域联想或自我推翻？

输出格式：
目标感：[高/中/低]，证据：[最少80字，说完为止，宁少勿水]
闭环感：[高/中/低]，证据：[最少80字，说完为止，宁少勿水]
沉浸感：[高/中/低]，证据：[最少80字，说完为止，宁少勿水]
成长感：[高/中/低]，证据：[最少80字，说完为止，宁少勿水]

关键约束：
- 不接收任何数据表格
- 不做数值计算
- 不输出 JSON（纯文本模糊匹配）
- 证据必须来自对话原文，禁止编造原话'''

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def analyze(self, messages: List[Dict], session_id: str = None) -> Optional[SessionAnalysis]:
        """分析对话，返回4维判定"""
        dialog_text = self._format_messages(messages)
        prompt = f"{self.PROMPT_TEMPLATE}\n\n对话原文：\n{dialog_text}"
        start = time.time()
        response = self.llm_client.chat(prompt)
        latency = int((time.time() - start) * 1000)
        result = self._parse_response(response)
        if result and session_id:
            result.session_id = session_id
        
        # 证据质量校验：只检查基本长度
        if result:
            for dim_name, ev in [
                ('目标对齐', result.goal_evidence),
                ('闭环指数', result.closure_evidence),
                ('心流深度', result.flow_evidence),
                ('认知成长', result.cognition_evidence)
            ]:
                if not ev or len(ev.strip()) < 20:
                    raise ValueError(f"{dim_name}证据过短({len(ev) if ev else 0}字)，拒绝写入")
        
        return result

    def _format_messages(self, messages: List[Dict]) -> str:
        """格式化消息列表为对话文本，超长时截断保留最近30轮"""
        if len(messages) > 60:
            messages = messages[-60:]
        lines = []
        for m in messages:
            role = m.get('role', 'unknown')
            content = (m.get('content') or '')[:500]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _parse_response(self, response: str) -> Optional[SessionAnalysis]:
        """解析 LLM 返回的文本"""
        if not response:
            return None
        pattern = r'(目标感|闭环感|沉浸感|成长感)[:：]\s*([高中低])[，,]\s*证据[:：]\s*(.+?)(?=\n(目标感|闭环感|沉浸感|成长感)|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        if len(matches) != 4:
            print(f"[解析警告] 只匹配到 {len(matches)} 个维度，原始响应：{response[:300]}")
            return None
        dim_map = {m[0]: (m[1], m[2].strip()) for m in matches}
        return SessionAnalysis(
            goal_alignment=dim_map.get('目标感', ('中', ''))[0],
            closure_index=dim_map.get('闭环感', ('中', ''))[0],
            flow_depth=dim_map.get('沉浸感', ('中', ''))[0],
            cognition_growth=dim_map.get('成长感', ('中', ''))[0],
            goal_evidence=dim_map.get('目标感', ('', ''))[1],
            closure_evidence=dim_map.get('闭环感', ('', ''))[1],
            flow_evidence=dim_map.get('沉浸感', ('', ''))[1],
            cognition_evidence=dim_map.get('成长感', ('', ''))[1]
        )