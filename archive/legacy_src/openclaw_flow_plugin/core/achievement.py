"""Achievement-fit and drift calculations (PRD chapter 2)."""

from dataclasses import dataclass


@dataclass
class AchievementResult:
    achievement_fit: float
    drift_rate: float | None


def calculate_achievement_fit(short_term: float, mid_term: float, long_term: float) -> float:
    """PRD: fit = short*0.3 + mid*0.3 + long*0.4."""
    return short_term * 0.3 + mid_term * 0.3 + long_term * 0.4


def calculate_drift_rate(drift_minutes: float, focus_minutes: float) -> float | None:
    """
    PRD:
    drift_rate = drift / (drift + focus) * 100
    if active time is 0 -> None (do not output).
    """
    total_active = drift_minutes + focus_minutes
    if total_active <= 0:
        return None
    return drift_minutes / total_active * 100.0


def calculate_achievement_result(
    short_term: float, mid_term: float, long_term: float, drift_minutes: float, focus_minutes: float
) -> AchievementResult:
    fit = calculate_achievement_fit(short_term, mid_term, long_term)
    drift = calculate_drift_rate(drift_minutes, focus_minutes)
    return AchievementResult(achievement_fit=fit, drift_rate=drift)


class AchievementFitCalculator:
    """成就拟合计算器"""
    
    def __init__(self):
        pass
    
    def calculate_fit(self, short_term: float, mid_term: float, long_term: float) -> float:
        """计算成就拟合度"""
        return calculate_achievement_fit(short_term, mid_term, long_term)
    
    def calculate_drift(self, drift_minutes: float, focus_minutes: float) -> float | None:
        """计算漂移率"""
        return calculate_drift_rate(drift_minutes, focus_minutes)
    
    def calculate_result(self, short_term: float, mid_term: float, long_term: float,
                         drift_minutes: float, focus_minutes: float) -> AchievementResult:
        """计算成就结果"""
        return calculate_achievement_result(short_term, mid_term, long_term, drift_minutes, focus_minutes)