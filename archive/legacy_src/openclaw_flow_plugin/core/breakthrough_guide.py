"""Breakthrough guide generator for different types."""

from typing import Dict, List, Any

TYPE_RECOMMENDATIONS = {
    "完美型": {
        "problems": [
            {"type": "持续进化", "evidence": "五维全高，需保持领先优势",
             "tool": "OKR目标管理", "action": "设定挑战性目标推动突破",
             "time_saving": "10天/年", "learning_cost": 8}
        ],
        "max_return_tool": "OKR目标管理",
        "quick_wins": ["定期复盘优化流程", "引入AI辅助决策"]
    },
    "高效产出型": {
        "problems": [
            {"type": "认知停滞", "evidence": "产出高但认知进化低",
             "tool": "费曼学习法", "action": "输出倒逼输入，强制知识外化",
             "time_saving": "15天/年", "learning_cost": 12}
        ],
        "max_return_tool": "费曼学习法",
        "quick_wins": ["每周写技术博客", "参与技术分享"]
    },
    "深度思考型": {
        "problems": [
            {"type": "心流破碎", "evidence": "认知活跃但心流状态不稳",
             "tool": "深潜模式", "action": "每日设定90分钟无打扰时段",
             "time_saving": "12天/年", "learning_cost": 4}
        ],
        "max_return_tool": "深潜模式",
        "quick_wins": ["开启免打扰模式", "批量处理消息"]
    },
    "战略清晰型": {
        "problems": [
            {"type": "执行薄弱", "evidence": "战略清晰但EWCI低",
             "tool": "PDCA闭环", "action": "建立每日闭环检查机制",
             "time_saving": "20天/年", "learning_cost": 6}
        ],
        "max_return_tool": "PDCA闭环",
        "quick_wins": ["任务拆分为可验证产出", "每日复盘完成情况"]
    },
    "盲目高效型": {
        "problems": [
            {"type": "目标漂移", "evidence": "效率高但目标拟合度低",
             "tool": "目标对齐工具", "action": "每周重新校准目标优先级",
             "time_saving": "25天/年", "learning_cost": 6}
        ],
        "max_return_tool": "目标对齐工具",
        "quick_wins": ["每日开始前确认3个核心任务", "删除非核心工作"]
    },
    "机械执行型": {
        "problems": [
            {"type": "缺乏深度", "evidence": "产出稳定但心流认知双低",
             "tool": "深度工作法", "action": "减少琐碎任务，增加深度时间",
             "time_saving": "18天/年", "learning_cost": 10}
        ],
        "max_return_tool": "深度工作法",
        "quick_wins": ["合并同类任务", "设置专注时段"]
    },
    "空想型": {
        "problems": [
            {"type": "执行力不足", "evidence": "状态好但产出低",
             "tool": "最小可行产出", "action": "将想法转化为可交付成果",
             "time_saving": "22天/年", "learning_cost": 8}
        ],
        "max_return_tool": "最小可行产出",
        "quick_wins": ["每个想法写一页方案", "设定产出截止时间"]
    },
    "低效忙碌型": {
        "problems": [
            {"type": "目标认知双缺失", "evidence": "心流好但目标认知低",
             "tool": "时间块管理", "action": "按目标分配时间，拒绝无效忙碌",
             "time_saving": "30天/年", "learning_cost": 8}
        ],
        "max_return_tool": "时间块管理",
        "quick_wins": ["用番茄钟分割时间", "记录时间消耗"]
    },
    "探索型": {
        "problems": [
            {"type": "试错期优化", "evidence": "目标认知高但心流产出低",
             "tool": "敏捷迭代", "action": "快速试错，及时调整方向",
             "time_saving": "15天/年", "learning_cost": 10}
        ],
        "max_return_tool": "敏捷迭代",
        "quick_wins": ["设定MVP标准", "定期回顾调整"]
    },
    "游击型": {
        "problems": [
            {"type": "稳定性不足", "evidence": "产出认知高但目标心流低",
             "tool": "节奏管理", "action": "建立稳定工作节奏，减少波动",
             "time_saving": "18天/年", "learning_cost": 6}
        ],
        "max_return_tool": "节奏管理",
        "quick_wins": ["固定工作时间段", "建立日常仪式"]
    },
    "闭关型": {
        "problems": [
            {"type": "目标失焦", "evidence": "心流认知高但目标产出低",
             "tool": "成果导向", "action": "将深度思考转化为可见成果",
             "time_saving": "20天/年", "learning_cost": 8}
        ],
        "max_return_tool": "成果导向",
        "quick_wins": ["设定可量化产出目标", "每周展示成果"]
    },
    "停滞型": {
        "problems": [
            {"type": "系统重启", "evidence": "五维全低，需全面调整",
             "tool": "彻底复盘", "action": "暂停工作，重新审视方向",
             "time_saving": "35天/年", "learning_cost": 16}
        ],
        "max_return_tool": "彻底复盘",
        "quick_wins": ["进行一周反思期", "寻求外部反馈"]
    },
    "勤奋破坏型": {
        "problems": [
            {"type": "方向错误", "evidence": "能力强但方向严重错误",
             "tool": "战略校准", "action": "立即停止当前方向，重新评估目标",
             "time_saving": "40天/年", "learning_cost": 12}
        ],
        "max_return_tool": "战略校准",
        "quick_wins": ["紧急战略会议", "暂停非核心项目"]
    }
}


def generate_breakthrough_guide(type_name: str) -> Dict[str, Any]:
    """Generate breakthrough guide based on type."""
    recommendations = TYPE_RECOMMENDATIONS.get(type_name, TYPE_RECOMMENDATIONS["停滞型"])
    
    return {
        "type_name": type_name,
        "problems": recommendations["problems"],
        "max_return_tool": recommendations["max_return_tool"],
        "quick_wins": recommendations["quick_wins"]
    }


def format_problems_as_text(problems: List[Dict[str, str]]) -> str:
    """Format problem diagnosis as text."""
    lines = []
    lines.append("【问题诊断】")
    lines.append("| 问题类型 | 推荐工具 | 行动建议 | 年节省时间 | 学习成本 |")
    lines.append("|----------|----------|----------|-----------|----------|")
    for p in problems:
        lines.append(f"| {p['type']}（{p['evidence']}） | **{p['tool']}**（{p['action']}） | {p['time_saving']} | {p['learning_cost']}小时 |")
    return "\n".join(lines)


def format_actions_as_text(max_return: str, quick_wins: List[str]) -> str:
    """Format action recommendations as text."""
    lines = []
    lines.append("【开始行动】")
    lines.append(f"最大回报工具：{max_return}")
    lines.append(f"即插即用工具：{', '.join(quick_wins)}")
    return "\n".join(lines)


def generate_methodology_upgrade(plan_changes: List[str]) -> str:
    """Generate methodology upgrade suggestion."""
    lines = []
    lines.append("🧬 方法论级升级建议（连续3次双环学习触发）")
    lines.append("")
    lines.append("你的认知框架正在发生结构性改变：")
    for change in plan_changes:
        lines.append(f"  【{change}】")
    lines.append("")
    lines.append("建议行动：")
    lines.append("  1. 将新方法固化为模板（写入OpenClaw/memory.md）")
    lines.append("  2. 在下个任务中刻意使用新方法，验证稳定性")
    lines.append("  3. 若连续2周稳定运行，升级为\"个人操作系统V2.0\"")
    lines.append("")
    lines.append("预期收益：该方法论若稳定运行，年化节省约20-30个工作日")
    return "\n".join(lines)


class BreakthroughGuide:
    """突破指南生成器"""
    
    def __init__(self):
        pass
    
    def generate(self, type_name: str) -> Dict[str, Any]:
        """生成突破指南"""
        return generate_breakthrough_guide(type_name)
    
    def format_problems(self, problems: List[Dict[str, str]]) -> str:
        """格式化问题诊断"""
        return format_problems_as_text(problems)
    
    def format_actions(self, max_return: str, quick_wins: List[str]) -> str:
        """格式化行动建议"""
        return format_actions_as_text(max_return, quick_wins)
    
    def generate_methodology_upgrade(self, plan_changes: List[str]) -> str:
        """生成方法论升级建议"""
        return generate_methodology_upgrade(plan_changes)