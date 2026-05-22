import json
import re
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
from plugin.session_analyzer import SessionAnalysis
from plugin.state_distiller import StatePortrait


@dataclass
class DimensionEvidence:
    level: str
    text: str
    trend: str = ""


@dataclass
class BreakthroughGuide:
    vulnerabilities: List[Dict]
    max_return_tool: str
    quick_win_tool: str
    annual_recovery: str


@dataclass
class FlowReport:
    date: str
    time_range: str
    summary: str
    rule_insight: str
    goal: DimensionEvidence
    closure: DimensionEvidence
    flow: DimensionEvidence
    cognition: DimensionEvidence
    breakthrough: BreakthroughGuide
    tuning_text: str


class ReportGenerator:
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def generate(self, analysis, portrait, trends=None, messages=None, time_range="当天"):
        polished = self._polish_portrait(portrait, analysis, messages)
        breakthrough = self._generate_breakthrough(portrait, analysis, messages)
        
        def make_ev(level, text, key):
            return DimensionEvidence(level, text, trends.get(key, "") if trends else "")
        
        return FlowReport(
            date=datetime.now().strftime("%Y-%m-%d"),
            time_range=time_range,
            summary=polished["summary"],
            rule_insight=polished["rule_insight"],
            goal=make_ev(analysis.goal_alignment, analysis.goal_evidence, "goal"),
            closure=make_ev(analysis.closure_index, analysis.closure_evidence, "closure"),
            flow=make_ev(analysis.flow_depth, analysis.flow_evidence, "flow"),
            cognition=make_ev(analysis.cognition_growth, analysis.cognition_evidence, "cognition"),
            breakthrough=breakthrough,
            tuning_text=portrait.tuning_text
        )
    
    def _polish_portrait(self, portrait, analysis, messages):
        recent = ""
        if messages and len(messages) >= 2:
            recent = "\n".join([f"{m['role']}: {m['content'][:50]}" for m in messages[-3:]])
        
        prompt = f"""你是 Flow 系统叙事师。

状态：{portrait.label}
描述：{portrait.description}
洞察：{portrait.rule_insight}
建议：{portrait.suggestion}
4维：目标{analysis.goal_alignment}（{analysis.goal_evidence}）闭环{analysis.closure_index}（{analysis.closure_evidence}）心流{analysis.flow_depth}（{analysis.flow_evidence}）认知{analysis.cognition_growth}（{analysis.cognition_growth}）
对话：{recent}

输出严格JSON（禁止多余内容）：
{{"summary": "标签 —— 描述。建议：...", "rule_insight": "洞察"}}"""
        
        raw = self.llm_client.generate(prompt)
        return self._safe_parse_json(raw, ["summary", "rule_insight"])
    
    def _generate_breakthrough(self, portrait, analysis, messages):
        evidence = ""
        if messages:
            evidence = " | ".join([f"{m['role']}: {m['content'][:50]}" for m in messages[-5:]])
        
        prompt = f"""你是 Flow 系统破局顾问。

【核心原则】
工具不是"推荐"出来的，是从今天的损失里长出来的。
根据对话中的具体损失，推荐能堵住漏洞的真实工具/方法。

【输入数据】
- 当前状态：{portrait.label}
- 4维判定：目标{analysis.goal_alignment}、闭环{analysis.closure_index}、心流{analysis.flow_depth}、认知{analysis.cognition_growth}
- 对话证据：{evidence}

【任务】
识别 3 个当前最大漏洞，每个漏洞匹配 1 个真实存在的工具/方法。

【铁律】
1. 问题描述必须包含：时间范围 + 具体行为 + 量化数据
2. 推荐工具必须真实存在，禁止编造。附来源（GitHub/官网）
3. 推荐理由必须解释：这个工具如何堵住漏洞
4. 节省时间基于对话证据推算：每天浪费 × 250工作日 = 年度节省
5. 学习成本基于该工具的实际入门时间估算
6. 禁止用"数据显示"、"研究表明"等话术

【输出格式】（严格按此，纯文本）：
VULNERABILITY_1: [8-15字问题类型]（[时间范围] [具体行为] [量化数据]）
TOOL_1: [工具名]（[30字内作用描述]）
REASON_1: [推荐理由，30字内]
TIME_SAVED_1: [X] 天/年
LEARNING_COST_1: [X] 小时
SOURCE_1: [工具来源，如 GitHub/官网]

VULNERABILITY_2: ...
TOOL_2: ...
REASON_2: ...
TIME_SAVED_2: ...
LEARNING_COST_2: ...
SOURCE_2: ...

VULNERABILITY_3: ...
TOOL_3: ...
REASON_3: ...
TIME_SAVED_3: ...
LEARNING_COST_3: ...
SOURCE_3: ...

MAX_RETURN: [工具名] → [20字内具体动作，今晚就能做]
QUICK_WIN: [工具名] → [20字内具体动作，今晚就能做]"""
        
        raw = self.llm_client.generate(prompt)
        return self._parse_breakthrough_v4(raw)
    
    def _parse_breakthrough_v4(self, text: str) -> BreakthroughGuide:
        lines = text.strip().split('\n')
        raw_data = {}
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                raw_data[key.strip().upper()] = value.strip()
        
        vulnerabilities = []
        total_saved = 0
        total_learning = 0.0
        
        for i in range(1, 4):
            v_key = f"VULNERABILITY_{i}"
            t_key = f"TOOL_{i}"
            r_key = f"REASON_{i}"
            ts_key = f"TIME_SAVED_{i}"
            lc_key = f"LEARNING_COST_{i}"
            
            if v_key not in raw_data:
                continue
            
            time_str = raw_data.get(ts_key, "0")
            try:
                time_saved = int(re.search(r'\d+', time_str).group())
            except:
                time_saved = 0
            
            cost_str = raw_data.get(lc_key, "0")
            try:
                learning_cost = float(re.search(r'\d+\.?\d*', cost_str).group())
            except:
                learning_cost = 0.0
            
            total_saved += time_saved
            total_learning += learning_cost
            
            tool_val = raw_data.get(t_key, "")
            tool_name = tool_val.split('（')[0] if '（' in tool_val else tool_val
            tool_desc = tool_val.split('（')[1].replace('）', '') if '（' in tool_val else ""
            
            vulnerabilities.append({
                "priority": f"🔴 {i}",
                "problem": raw_data[v_key],
                "tool": f"**{tool_name}**（{tool_desc}）" if tool_desc else f"**{tool_name}**",
                "reason": raw_data.get(r_key, ""),
                "time_saved": f"{time_saved} 天/年",
                "learning_cost": f"{learning_cost} 小时"
            })
        
        annual_recovery = min(total_saved, 250)
        max_return = raw_data.get("MAX_RETURN", "")
        quick_win = raw_data.get("QUICK_WIN", "")
        roi = f"{total_saved}:{int(total_learning)}" if total_learning > 0 else "N/A"
        
        return BreakthroughGuide(
            vulnerabilities=vulnerabilities,
            max_return_tool=max_return,
            quick_win_tool=quick_win,
            annual_recovery=f"{annual_recovery} 个工作日 | 学习成本：{total_learning} 小时 | 投入回报率：约 {roi}"
        )
    
    def _safe_parse_json(self, raw_text: str, required_keys: List[str]) -> Dict:
        cleaned = re.sub(r'```json\s*|\s*```', '', raw_text).strip()
        
        try:
            data = json.loads(cleaned)
            for key in required_keys:
                if key not in data:
                    raise KeyError(key)
            return data
        except Exception:
            extracted = {}
            for key in required_keys:
                pattern = rf'"{key}"\s*:\s*"([^"]+)"'
                match = re.search(pattern, cleaned)
                if match:
                    extracted[key] = match.group(1)
            
            if extracted:
                for key in required_keys:
                    if key not in extracted:
                        extracted[key] = ""
                return extracted
            
            return {k: "" for k in required_keys}
    
    def format_markdown(self, report: FlowReport) -> str:
        def dim_line(name, icon, ev):
            t = f" {ev.trend}" if ev.trend else ""
            return f"{icon} {name}：{ev.level}（{ev.text}）{t}"
        
        rows = ""
        for v in report.breakthrough.vulnerabilities:
            rows += f"| {v['priority']} | {v['problem']} | {v['tool']} | {v['reason']} | {v['time_saved']} | {v['learning_cost']} |\n"
        
        total_saved = sum(int(v['time_saved'].replace(' 天/年', '')) for v in report.breakthrough.vulnerabilities)
        
        return f"""📅 Flow 系统认知镜像 ({report.date})

时间范围：{report.time_range}

**总结摘要**：{report.summary}

**四维评估**：
{dim_line("目标对齐", "🎯", report.goal)}
{dim_line("闭环指数", "🔄", report.closure)}
{dim_line("心流深度", "💫", report.flow)}
{dim_line("认知成长", "🧠", report.cognition)}

**规则洞察**：
{report.rule_insight}

💡 **破局指南**

━━━━━━━━━━━━━━━━━━━━━━
**当前最大漏洞**

| 优先级 | 问题类型 | 推荐工具或方法 | 推荐理由 | 节省时间（年） | 学习成本 |
|--------|----------|----------------|----------|----------------|----------|
{rows}> **年度节省上限说明**：三项合计 {total_saved} 天/年，实际可节省上限为 250 天/年（受限于工作日）。

━━━━━━━━━━━━━━━━━━━━━━
**开始行动**

最大回报工具：{report.breakthrough.max_return_tool}
即插即用工具：{report.breakthrough.quick_win_tool}
年度节省：{report.breakthrough.annual_recovery}

━━━━━━━━━━━━━━━━━━━━━━
> 这份报告由 Flow Ecosystem 自动生成。它不评判你，只是帮你看见自己的节奏。
"""