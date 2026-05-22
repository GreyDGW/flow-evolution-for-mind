"""Time-factor calculation (PRD 4.5)."""

import math

T0_MINUTES = 5.0
T_MAX_MINUTES = 180.0


def calculate_time_factor(total_effective_minutes: float) -> float:
    """
    PRD formula:
    时间系数 = min( ln(1 + t/T0) / ln(1 + Tmax/T0), 1.0 )
    """
    if total_effective_minutes <= 0:
        return 0.0

    numerator = math.log(1.0 + total_effective_minutes / T0_MINUTES)
    denominator = math.log(1.0 + T_MAX_MINUTES / T0_MINUTES)
    return min(numerator / denominator, 1.0)


class FlowTimeFactor:
    """心流时间因素计算器"""
    
    def __init__(self):
        self.total_effective_minutes = 0.0
    
    def add_effective_time(self, minutes: float):
        """添加有效时间"""
        self.total_effective_minutes += minutes
    
    def calculate(self) -> float:
        """计算时间系数"""
        return calculate_time_factor(self.total_effective_minutes)
    
    def reset(self):
        """重置时间"""
        self.total_effective_minutes = 0.0