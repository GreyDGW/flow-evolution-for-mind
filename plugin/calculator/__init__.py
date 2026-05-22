"""Flow Ecosystem - Calculator Module

综合指数计算：
- power: 动力计算
- ewci: 闭环指数（函数）
- strategic_index: 战略指数
- flow_quality: 心流质量
- flow_time_factor: 时间系数
- flow_segment: 片段分割
"""

from .power import PowerCalculator as Power
from .ewci import calculate_ewci as calculate_ewci_func, calculate_closure_completeness
from .strategic_index import StrategicIndexCalculator as StrategicIndex

class EWCI:
    @staticmethod
    def calculate(efficiency, quantity, quality, complexity_coeff):
        return calculate_ewci_func(efficiency, quantity, quality, complexity_coeff)
    
    @staticmethod
    def closure_completeness(plan, do_check, adjust):
        return calculate_closure_completeness(plan, do_check, adjust)

__all__ = [
    "Power",
    "EWCI",
    "StrategicIndex",
]