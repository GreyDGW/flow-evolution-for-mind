"""Five-dimensional assessment report generator."""

from typing import Dict, List, Any
from .type_matcher import match_type

STRATEGIC_LEVEL_MAP = {
    "卓越": "🎯",
    "达成": "✅",
    "偏离": "⚠️",
    "失效": "❌"
}

EXECUTION_LEVEL_MAP = {
    "S": "🏆",
    "A": "⭐",
    "B": "📊",
    "C": "📉",
    "D": "❌"
}

STATE_LEVEL_MAP = {
    "高": "🟢",
    "中": "🟡",
    "低": "🟠",
    "危": "🔴"
}


def get_strategic_level(score: float) -> str:
    """Map score to strategic level."""
    if score >= 75:
        return "卓越"
    elif score >= 50:
        return "达成"
    elif score >= 25:
        return "偏离"
    else:
        return "失效"


def get_execution_level(score: float) -> str:
    """Map score to execution level."""
    if score >= 90:
        return "S"
    elif score >= 65:
        return "A"
    elif score >= 40:
        return "B"
    elif score >= 20:
        return "C"
    else:
        return "D"


def get_state_level(score: float) -> str:
    """Map score to state level."""
    if score >= 75:
        return "高"
    elif score >= 50:
        return "中"
    elif score >= 25:
        return "低"
    else:
        return "危"


def generate_five_dimension_table(
    navigation_percent: float,
    achievement_fit: float,
    ewci: float,
    flow_index: float,
    cognitive_evolution: float
) -> List[Dict[str, str]]:
    """Generate five-dimensional assessment table."""
    
    def get_quick_judgment(score: float) -> str:
        return "高" if score >= 70 else "低"
    
    def generate_comment(dimension: str, score: float, level: str) -> str:
        comments = {
            "Navigation系数": {
                "卓越": "方向高度正确",
                "达成": "方向基本正确",
                "偏离": "方向需调整",
                "失效": "方向严重错误"
            },
            "目标拟合度": {
                "卓越": "目标高度契合",
                "达成": "目标基本契合",
                "偏离": "目标存在偏差",
                "失效": "目标完全偏离"
            },
            "外部闭环效率": {
                "S": "闭环高效",
                "A": "闭环良好",
                "B": "闭环中等",
                "C": "闭环低效",
                "D": "闭环失效"
            },
            "心流指数": {
                "高": "状态极佳",
                "中": "状态良好",
                "低": "状态薄弱",
                "危": "状态危急"
            },
            "认知进化指数": {
                "高": "认知活跃",
                "中": "认知稳步",
                "低": "认知停滞",
                "危": "认知倒退"
            }
        }
        return comments[dimension].get(level, "需关注")[:10]
    
    table = [
        {
            "维度": "Navigation系数",
            "数值": f"{navigation_percent:.1f}",
            "快速判定": get_quick_judgment(navigation_percent),
            "详细层级": STRATEGIC_LEVEL_MAP[get_strategic_level(navigation_percent)],
            "评价": generate_comment("Navigation系数", navigation_percent, get_strategic_level(navigation_percent))
        },
        {
            "维度": "目标拟合度",
            "数值": f"{achievement_fit:.1f}",
            "快速判定": get_quick_judgment(achievement_fit),
            "详细层级": STRATEGIC_LEVEL_MAP[get_strategic_level(achievement_fit)],
            "评价": generate_comment("目标拟合度", achievement_fit, get_strategic_level(achievement_fit))
        },
        {
            "维度": "外部闭环效率",
            "数值": f"{ewci:.1f}",
            "快速判定": get_quick_judgment(ewci),
            "详细层级": EXECUTION_LEVEL_MAP[get_execution_level(ewci)],
            "评价": generate_comment("外部闭环效率", ewci, get_execution_level(ewci))
        },
        {
            "维度": "心流指数",
            "数值": f"{flow_index:.1f}",
            "快速判定": get_quick_judgment(flow_index),
            "详细层级": STATE_LEVEL_MAP[get_state_level(flow_index)],
            "评价": generate_comment("心流指数", flow_index, get_state_level(flow_index))
        },
        {
            "维度": "认知进化指数",
            "数值": f"{cognitive_evolution:.1f}",
            "快速判定": get_quick_judgment(cognitive_evolution),
            "详细层级": STATE_LEVEL_MAP[get_state_level(cognitive_evolution)],
            "评价": generate_comment("认知进化指数", cognitive_evolution, get_state_level(cognitive_evolution))
        }
    ]
    
    return table


def format_table_as_text(table: List[Dict[str, str]]) -> str:
    """Format assessment table as text."""
    lines = []
    lines.append("| 维度 | 数值 | 快速判定 | 详细层级 | 评价 |")
    lines.append("|------|------|----------|----------|------|")
    for row in table:
        lines.append(f"| {row['维度']} | {row['数值']} | {row['快速判定']} | {row['详细层级']} | {row['评价']} |")
    return "\n".join(lines)


def generate_type_determination(
    navigation_percent: float,
    achievement_fit: float,
    ewci: float,
    flow_index: float,
    cognitive_evolution: float,
    power: float,
    strategic_index: float
) -> Dict[str, Any]:
    """Generate type determination output."""
    matched_type = match_type(navigation_percent, achievement_fit, ewci, flow_index, cognitive_evolution)
    
    return {
        "type_name": matched_type["name"],
        "type_description": matched_type["description"],
        "navigation": {
            "value": navigation_percent,
            "level": get_strategic_level(navigation_percent),
            "icon": STRATEGIC_LEVEL_MAP[get_strategic_level(navigation_percent)]
        },
        "power": power,
        "strategic_index": strategic_index,
        "strategic_level": get_strategic_level(strategic_index),
        "strategic_icon": STRATEGIC_LEVEL_MAP[get_strategic_level(strategic_index)]
    }


def format_type_determination_as_text(result: Dict[str, Any]) -> str:
    """Format type determination as text."""
    lines = []
    lines.append(f"今日你是【{result['type_name']}】，{result['type_description']}")
    lines.append("")
    lines.append(f"Navigation = {result['navigation']['value']:.1f}（{result['navigation']['icon']} {result['navigation']['level']}）")
    lines.append(f"Power = {result['power']:.1f}")
    lines.append(f"综合指数 = {result['strategic_index']:.1f}（{result['strategic_icon']} {result['strategic_level']}）")
    return "\n".join(lines)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        pass
    
    def generate_five_dimension_report(self, navigation_percent: float, achievement_fit: float,
                                       ewci: float, flow_index: float, cognitive_evolution: float) -> str:
        """生成五维评估报告"""
        table = generate_five_dimension_table(navigation_percent, achievement_fit, ewci, flow_index, cognitive_evolution)
        return format_table_as_text(table)
    
    def generate_type_report(self, navigation_percent: float, achievement_fit: float, ewci: float,
                            flow_index: float, cognitive_evolution: float, power: float,
                            strategic_index: float) -> str:
        """生成类型判定报告"""
        result = generate_type_determination(navigation_percent, achievement_fit, ewci, flow_index,
                                             cognitive_evolution, power, strategic_index)
        return format_type_determination_as_text(result)