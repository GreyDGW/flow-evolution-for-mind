from typing import Tuple


def calculate_navigation_raw(achievement_fit: float, drift_rate: float, cognitive_level: str = "中") -> float:
    exemptions = {"高": 0.5, "中": 0.8, "低": 1.0, "危": 1.0}
    exemption = exemptions.get(cognitive_level, 1.0)
    return (achievement_fit / 100 * (1 - drift_rate / 100 * exemption) * 2) - 1


def navigation_to_percent(navigation_raw: float) -> float:
    return (navigation_raw + 1) * 50


def get_navigation_level(percent: float) -> Tuple[str, str]:
    if percent >= 75:
        return ("卓越", "🎯")
    elif percent >= 50:
        return ("达成", "✅")
    elif percent >= 25:
        return ("偏离", "⚠️")
    else:
        return ("失效", "❌")


def calculate_goal_alignment(short_term: float, medium_term: float, long_term: float) -> float:
    return short_term * 0.3 + medium_term * 0.3 + long_term * 0.4


def calculate_drift_rate(drift_time: float, focus_time: float) -> float:
    total = drift_time + focus_time
    if total == 0:
        return 0.0
    return (drift_time / total) * 100


def get_drift_level(drift_rate: float) -> Tuple[str, str]:
    if drift_rate < 20:
        return ("卓越", "🎯")
    elif drift_rate < 40:
        return ("达成", "✅")
    elif drift_rate < 60:
        return ("偏离", "⚠️")
    else:
        return ("失效", "❌")


class NavigationCalculator:
    """导航计算器"""
    
    def __init__(self):
        pass
    
    def calculate(self, achievement_fit: float, drift_rate: float, cognitive_level: str = "中") -> dict:
        """计算导航指数"""
        raw = calculate_navigation_raw(achievement_fit, drift_rate, cognitive_level)
        percent = navigation_to_percent(raw)
        level, icon = get_navigation_level(percent)
        
        return {
            'raw_score': raw,
            'percent': percent,
            'level': level,
            'icon': icon
        }
    
    def calculate_alignment(self, short_term: float, medium_term: float, long_term: float) -> float:
        """计算目标对齐度"""
        return calculate_goal_alignment(short_term, medium_term, long_term)