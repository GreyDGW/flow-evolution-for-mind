import math
from typing import Tuple

def calculate_efficiency(active_work_minutes: float, total_period_minutes: float, avg_output_coefficient: float) -> float:
    if total_period_minutes == 0:
        return 0.0
    return (active_work_minutes / total_period_minutes) * avg_output_coefficient

def calculate_quantity(closure_count: int) -> float:
    return 1 + math.log(1 + min(closure_count, 10)) / 3

def calculate_quality(avg_completeness: float) -> float:
    return avg_completeness / 100

def calculate_complexity_coefficient(task_complexity: float, output_value: float, time_ratio: float) -> float:
    base = (task_complexity / 10 * 0.4 + output_value / 10 * 0.4 + min(time_ratio, 2) / 2 * 0.2)
    
    if task_complexity >= 7 and output_value >= 7:
        return base * 1.2
    elif task_complexity <= 3 and output_value <= 3:
        return base * 0.6
    else:
        return base

def calculate_ewci(efficiency: float, quantity: float, quality: float, complexity_coeff: float) -> float:
    return efficiency * quantity * quality * complexity_coeff * 100

def calculate_closure_completeness(plan_score: float, do_score: float, check_score: float, adjust_score: float) -> float:
    return plan_score * 0.2 + do_score * 0.3 + check_score * 0.2 + adjust_score * 0.3

def get_output_quality_level(level: str) -> float:
    levels = {"S": 1.0, "A": 0.9, "B": 0.7, "C": 0.4, "D": 0.0}
    return levels.get(level, 0.7)

def get_execution_level(score: float) -> Tuple[str, str]:
    if score >= 90:
        return ("S", "🏆")
    elif score >= 65:
        return ("A", "⭐")
    elif score >= 40:
        return ("B", "📊")
    elif score >= 20:
        return ("C", "📉")
    else:
        return ("D", "❌")