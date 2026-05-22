"""
TrendLLMAnalyzer：LLM 趋势归因层
职责：接收异常点，动态读取原文，调用 DeepSeek 生成归因 + 规律
"""
import os
import re
import sqlite3
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

SHARED_RULES = """
【铁律】
1. 只使用输入数据中的信息，禁止编造任何数字、百分比、价格、统计
2. 禁止替换关键词
3. 禁止发挥：不推测、不联想、不补充背景知识
4. 禁止用"数据显示"、"研究表明"、"历史记录"等话术
5. 语气：中性、克制、不热情
6. 证据必须来自对话原文，不编造
"""

class TrendLLMAnalyzer:
    def __init__(self, db_path: str = "data/flow_ecosystem.db"):
        self.db_path = db_path
        self.client = None
        self._init_llm()

    def _init_llm(self):
        try:
            from plugin.llm_client import DeepSeekLLMClient
            key = os.getenv('DEEPSEEK_API_KEY')
            if key:
                self.client = DeepSeekLLMClient(api_key=key)
        except Exception as e:
            print(f"[TrendLLM] LLM 客户端初始化失败: {e}")

    def analyze(self, anomalies: List[Dict], patterns: List[str]) -> Dict:
        if not self.client:
            return {"error": "LLM 客户端未配置", "mode": "未初始化"}

        if not anomalies:
            return {
                "mode": "无异常",
                "pattern": "",
                "attributions": [],
                "cross_pattern": "状态平稳，无明显波动",
                "suggestion": "保持当前节奏",
                "raw_response": ""
            }

        enriched = []
        for a in anomalies:
            a['context'] = self._extract_context(a['session_id'])
            enriched.append(a)

        prompt = self._build_prompt(enriched, patterns)

        try:
            response = self.client.chat(prompt)
            result = self._parse_response(response)
            result["raw_response"] = response
            return result
        except Exception as e:
            return {
                "error": f"LLM 调用失败: {str(e)[:50]}",
                "mode": "调用失败",
                "attributions": [],
                "cross_pattern": "",
                "suggestion": "",
                "raw_response": ""
            }

    def _extract_context(self, session_id: str, max_chars: int = 800) -> str:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
            SELECT role, content_text
            FROM sessions
            WHERE session_id = ?
              AND content_text IS NOT NULL
              AND content_text != ''
            ORDER BY timestamp ASC
        """, (session_id,))

        msgs = [dict(r) for r in c.fetchall()]
        conn.close()

        if not msgs:
            return "[无对话记录]"

        context_msgs = msgs[:4] + msgs[-2:] if len(msgs) > 6 else msgs

        lines = []
        for m in context_msgs:
            content = m['content_text']

            if '```' in content:
                parts = content.split('```')
                if len(parts) >= 3:
                    before = parts[0][:80]
                    after = parts[-1][:50] if parts[-1] else ''
                    content = f"{before}[代码片段...]{after}"

            if content.startswith('> ') and len(content) > 150:
                content = content[:150] + '...'

            content = re.sub(r'`[^`]{50,}`', '`[代码]...`', content)

            role = 'U' if m['role'] == 'user' else 'A'
            lines.append(f"{role}: {content[:180]}")

        return "\n".join(lines)[:max_chars]

    def _build_prompt(self, anomalies: List[Dict], patterns: List[str]) -> str:
        lines = []
        lines.append("你是 Flow 系统趋势分析师。")
        lines.append(SHARED_RULES)
        lines.append("")
        lines.append("以下是一组异常 session 的完整数据，请分析规律并给出洞察。")
        lines.append("每个异常点包含：维度判定、证据、以及对话原文上下文（已压缩代码块）。")
        lines.append("")

        for i, a in enumerate(anomalies, 1):
            lines.append("━━━━━━━━━━━━━━━━━━━━━━")
            created = a.get('created_at', '未知时间')
            lines.append(f"异常 [{i}] {created[:16]}")
            sid = a['session_id']
            lines.append(f"  Session: {sid[:20]}...")
            dim = a['dimension']
            val = a['value']
            reason = a['reason']
            z = a['z_score']
            lines.append(f"  维度: {dim} = {val}（{reason}，z={z}）")
            evidence = a.get('evidence', '无')
            lines.append(f"  证据: {evidence[:60]}")
            lines.append(f"  对话上下文:")
            ctx = a.get('context', '[无]')
            for cl in ctx.split('\n'):
                lines.append(f"    {cl}")
            lines.append("")

        if patterns:
            lines.append("已检测到的本地规律：")
            for p in patterns:
                lines.append(f"  • {p}")
            lines.append("")

        lines.append("分析要求：")
        lines.append("1. 找出共同模式（时间/主题/行为），30字内")
        lines.append("2. 逐点归因（每点30字内，必须基于原文证据，不编造）")
        lines.append("3. 跨点规律（50字内，连接多个异常点的共性）")
        lines.append("4. 总体建议（50字内，可执行）")
        lines.append("")
        lines.append("输出格式（严格按此格式，不要JSON，不要Markdown标题）：")
        lines.append(f"模式：[共同模式]")
        for i in range(1, len(anomalies) + 1):
            lines.append(f"归因_{i}：[30字内归因]")
        lines.append("规律：[跨点规律，50字内]")
        lines.append("建议：[总体建议，50字内]")

        return "\n".join(lines)

    def _parse_response(self, response: str) -> Dict:
        if not response:
            return {
                "mode": "解析失败", "pattern": "",
                "attributions": [], "cross_pattern": "", "suggestion": ""
            }

        result = {
            "mode": "有异常", "pattern": "",
            "attributions": [], "cross_pattern": "", "suggestion": ""
        }

        for line in response.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('模式：'):
                result['pattern'] = line.replace('模式：', '').strip()
            elif line.startswith('归因_'):
                parts = line.split('：', 1)
                if len(parts) == 2:
                    result['attributions'].append(parts[1].strip())
            elif line.startswith('规律：'):
                result['cross_pattern'] = line.replace('规律：', '').strip()
            elif line.startswith('建议：'):
                result['suggestion'] = line.replace('建议：', '').strip()

        return result