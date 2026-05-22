"""
ReportPolisher：LLM 润色层
职责：把全量 session 数据改写成第一人称自然语言
输入：sessions（含4维+evidence+原文）+ portrait + trend
输出：引语、4句具体表现、3个场景、整体建议
"""
import os
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()


SHARED_RULES = """
【铁律】
1. 只使用输入数据中的信息，禁止编造任何数字、百分比、价格、统计
2. 禁止替换关键词
3. 禁止发挥：不推测、不联想、不补充背景知识
4. 禁止用"数据显示"、"研究表明"、"历史记录"等话术
5. 语气：温和、陪伴、不评判，像朋友在复盘
6. 引语用"你"开头，像AI直接对用户说话
7. 场景必须包含具体时间戳和具体行为，基于原文，不编造
"""


class ReportPolisher:
    def __init__(self):
        self.client = None
        self._init_llm()

    def _init_llm(self):
        try:
            from plugin.llm_client import DeepSeekLLMClient
            key = os.getenv('LLM_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
            if key:
                self.client = DeepSeekLLMClient(api_key=key)
        except Exception as e:
            print(f"[Polisher] LLM 初始化失败: {e}")

    def polish(self, sessions: List[Dict], portrait: Dict, trend: Dict, insight: str = '', weak_summary: str = '') -> Dict:
        """
        主入口
        """
        if not self.client:
            return self._fallback(portrait, sessions)

        prompt = self._build_prompt(sessions, portrait, trend, insight, weak_summary)

        try:
            response = self.client.chat(prompt)
            return self._parse_response(response)
        except Exception as e:
            print(f"[Polisher] LLM 调用失败: {e}")
            return self._fallback(portrait, sessions)

    def _build_prompt(self, sessions: List[Dict], portrait: Dict, trend: Dict, insight: str, weak_summary: str) -> str:
        """构建 Prompt"""
        lines = []
        lines.append("你是用户的认知镜像复盘助手。")
        lines.append(SHARED_RULES)
        lines.append("")
        lines.append("根据以下对话数据，帮用户做一个友好的复盘。")
        lines.append("")

        # 画像信息
        lines.append("【画像】")
        lines.append(f"标签: {portrait.get('label', '未知')}")
        lines.append(f"描述: {portrait.get('description', '')}")
        lines.append("")

        # 分布洞察（如果有）
        if insight:
            lines.append("【分布洞察】")
            lines.append(insight)
            lines.append("")
            if weak_summary:
                lines.append("【短板 Session 摘要】")
                lines.append(weak_summary)
                lines.append("")

        # 近期对话
        lines.append("【近期对话】")
        for i, s in enumerate(sessions[:5], 1):
            raw_time = s.get('dialog_time') or s.get('created_at', '')
            time = raw_time[11:16] if len(raw_time) >= 16 else raw_time[:5]
            goal = s.get('goal_alignment', '')
            closure = s.get('closure_index', '')
            lines.append(f"[{i}] {time} | 目标:{goal} 闭环:{closure}")
            evidence = s.get('goal_evidence', '') or s.get('closure_evidence', '')
            if evidence:
                lines.append(f"       证据: {evidence[:50]}")
        lines.append("")

        # 趋势
        lines.append("【趋势】")
        for dim, info in trend.items():
            lines.append(f"  {dim}: {info}")
        lines.append("")


        lines.append("【引用原则——增加真实感】")
        lines.append("表现、场景、引语优先从 evidence 的原文片段中提取用户原话作为素材。")
        lines.append("evidence 中标注用户原话的部分，可直接引用或呼应。")
        lines.append("让用户听到自己的声音，不要只概括。")
        # 输出要求
        lines.append("请输出：")
        lines.append("1. 一句引语（用'你'开头，120字内，情绪层：整体肯定用户的努力，温柔指出修正成本。禁止包含任何行动建议、具体策略、或'建议''试试''可以'等词汇）")
        lines.append("2. 四句具体表现（每句用'你'开头，描述用户的具体行为，基于证据）")
        lines.append("3. 三个场景（如果分布洞察存在，全部聚焦短板；包含时间和行为，40字内）")
        lines.append("4. 一条整体建议（200字内，认知层/行动层：基于四维状态+趋势，给出1-2个具体可执行的行动建议。禁止重复引语中的情绪评价，禁止说'方向很准''洞察力让人佩服''修正成本'等引语内容，禁止总结已发生的行为，只面向未来给出行动策略）")
        lines.append("")
        lines.append("输出格式：")
        lines.append("引语：[120字内第一人称，整体肯定+温柔指出修正成本]")
        lines.append("表现1：[内容]")
        lines.append("表现2：[内容]")
        lines.append("表现3：[内容]")
        lines.append("表现4：[内容]")
        lines.append("场景1：[时间] [行为]")
        lines.append("场景2：[时间] [行为]")
        lines.append("场景3：[时间] [行为]")
        lines.append("建议：[200字内自然语言段落，独立总结，不重复引语]")

        return "\n".join(lines)

    def _parse_response(self, response: str) -> Dict:
        """解析响应"""
        result = {
            "quote": "",
            "performances": [],
            "scenes": [],
            "suggestion": ""
        }

        for line in response.strip().split('\n'):
            line = line.strip()
            if '引语' in line and '：' in line:
                result["quote"] = line.split('：', 1)[1].strip()
            elif line.startswith('表现') and '：' in line:
                parts = line.split('：', 1)
                if len(parts) == 2:
                    result["performances"].append(parts[1].strip())
            elif line.startswith('场景'):
                parts = line.split('：', 1)
                if len(parts) == 2:
                    result["scenes"].append(parts[1].strip())
            elif line.startswith('建议：'):
                result["suggestion"] = line.replace('建议：', '').strip()

        return result

    def _fallback(self, portrait: Dict, sessions: List[Dict]) -> Dict:
        """LLM不可用时的降级方案"""
        label = portrait.get('label', '未知')
        return {
            "quote": f"你最近处于「{label}」状态",
            "performances": [
                f"你近期的目标对齐度{portrait.get('goal_alignment', '适中')}",
                f"你在执行任务时{portrait.get('description', '表现平稳')}",
                f"你的心流状态{portrait.get('flow_depth', '适中')}",
                f"你在{len(sessions)}个会话中保持了持续的对话"
            ],
            "scenes": [
                f"最近一次会话中，你专注于当前任务",
                f"在此之前，你完成了{len(sessions)}个对话",
                f"根据分析，你的状态需要关注"
            ],
            "suggestion": portrait.get('suggestion', '保持当前节奏，继续观察')
        }