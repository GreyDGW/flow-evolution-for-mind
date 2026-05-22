from typing import List, Dict, Optional
import time
import re

class SessionAnalysis:
    def __init__(self, goal_alignment='', closure_index='', flow_depth='', cognition_growth='',
                 goal_evidence='', closure_evidence='', flow_evidence='', cognition_evidence='', session_id=None):
        self.goal_alignment = goal_alignment
        self.closure_index = closure_index
        self.flow_depth = flow_depth
        self.cognition_growth = cognition_growth
        self.goal_evidence = goal_evidence
        self.closure_evidence = closure_evidence
        self.flow_evidence = flow_evidence
        self.cognition_evidence = cognition_evidence
        self.session_id = session_id

class SessionAnalyzer:
    PROMPT_TEMPLATE = '''你是认知分析师。阅读以下对话后，从4个维度给出判定（只选 高/中/低），每维附一段证据。

【证据格式——State Change 单段式】
证据 80-300 字。像朋友复盘你的对话，不是审计报告。

只记录导致状态变更（State Change）的行为：
- 用户推翻了之前的想法
- 用户提出了新定义/新框架
- 用户拒绝了建议或方案
- 用户表达了强烈情绪或判断
- 用户做了意外的优先级调整
- 用户从A话题突然跳到B话题（话题漂移）

【禁止——违反会导致输出失败】
- 禁止流水账：不要按时间顺序罗列事件（"接着...然后...随后...最后..."）
- 禁止系统视角：不要描述"助手响应了什么"、"系统做了什么"
- 禁止纯形容词堆砌：不要"很好""明确""顺利"
- 禁止编造：原话必须真实存在

【写法要求】
先写最关键的 1-2 个 State Change（含时间戳 + 原话 + 为什么重要）。
如果还有空间（<300字），补充第3个。
写完即止，禁止硬凑到300字。

【内部审计——18项认知扫描点】
读对话时，请针对性扫描以下信号，它们是证据的核心来源：

1. 目标感 (Navigation)：
   - 方向稳定性（有无突然跳转话题）
   - 优先级清晰度（有无主动取舍目标）
   - 纠偏主动性（偏离后是否主动拉回）
   - 目标具象化（是否从想做什么转为怎么做）

2. 闭环感 (Closure - PDCA)：
   - 计划明确性(P)（有无定义首步动作）
   - 执行推进度(D)（有无实际决策操作）
   - 验证完整性(C)（有无结论产出）
   - 调整闭环度(A)（有无迭代修正）

3. 沉浸感 (Flow)：
   - 逻辑链深度（推理层级）
   - 有序度（讨论是否层层递进）
   - 追问持续性（是否追问到底）
   - 专注信号（有无连续深入迹象）
   - 元认知（有无反思方法论）

4. 成长感 (Cognition)：
   - 逻辑链条（推理长度）
   - 概念密度（新框架/新概念出现）
   - 自我修正（推翻旧判断）
   - 跨域连接（方法论迁移）
   - 方法论提炼（抽象出通用规则）

【输出要求】
严格按以下格式输出，不要JSON，不要Markdown标题：

目标感：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]
闭环感：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]
沉浸感：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]
成长感：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]

【对话原文】
{dialog_text}
'''

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def analyze(self, messages: List[Dict], session_id: str = None) -> Optional[SessionAnalysis]:
        dialog_text = self._format_messages(messages)
        prompt = self.PROMPT_TEMPLATE.format(dialog_text=dialog_text)
        start = time.time()
        response = self.llm_client.chat(prompt)
        latency = int((time.time() - start) * 1000)
        result = self._parse_response(response)
        if result and session_id:
            result.session_id = session_id
        
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
        lines = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '') or ''
            if content.strip():
                lines.append(f"[{role}]: {content}")
        return '\n'.join(lines)

    def _parse_response(self, response: str) -> Optional[SessionAnalysis]:
        if not response:
            return None
        
        # Markdown 清洗：去掉粗体、标题、分隔线等格式干扰
        response = response.replace('**', '').replace('__', '').replace('---', '')
        response = response.replace('### ', '').replace('## ', '').replace('# ', '')
        response = re.sub(r'<[^>]+>', '', response)
        
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