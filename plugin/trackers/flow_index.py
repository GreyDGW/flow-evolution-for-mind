import math
from typing import Tuple, List


def classify_interruption(duration_seconds: float) -> str:
    if duration_seconds < 120:
        return "micro"
    elif duration_seconds < 900:
        return "medium"
    else:
        return "heavy"


def calculate_effective_duration(duration_min: float, interruptions: List[str]) -> float:
    effective = duration_min
    for interrupt in interruptions:
        if interrupt == "micro":
            effective -= 3
        else:
            effective -= 15
    return max(effective, 0)


def calculate_base_quality_score(dimensions: List[float]) -> float:
    return sum(dimensions) / len(dimensions)


def calculate_signal_gain_coefficient(signals: List[float], rebellion_score: float = 0) -> float:
    raw_score = sum(signals) / 15
    coefficient = 1.0 + raw_score * 0.6
    if rebellion_score == 3:
        coefficient += 0.2
    return min(coefficient, 1.8)


def calculate_time_coefficient(total_effective_minutes: float) -> float:
    return min(math.log(1 + total_effective_minutes / 5) / math.log(1 + 180 / 5), 1.0)


def calculate_flow_index(weighted_quality: float, time_coeff: float) -> float:
    return weighted_quality * time_coeff * 100


def calculate_weighted_quality_score(fragments: List[dict]) -> float:
    if not fragments:
        return 0.0
    
    total_effective = sum(f['effective_duration'] for f in fragments)
    if total_effective == 0:
        return 0.0
    
    weighted_sum = sum(f['quality_score'] * f['effective_duration'] for f in fragments)
    return weighted_sum / total_effective


def get_flow_level(score: float) -> Tuple[str, str]:
    if score >= 75:
        return ("高", "🟢")
    elif score >= 50:
        return ("中", "🟡")
    elif score >= 25:
        return ("低", "🟠")
    else:
        return ("危", "🔴")


class FlowIndexCalculator:
    """心流指数计算器"""
    
    def __init__(self):
        pass
    
    def calculate(self, fragments: List[dict], signals: List[float] = None, 
                  rebellion_score: float = 0) -> dict:
        """计算心流指数"""
        if signals is None:
            signals = []
        
        weighted_quality = calculate_weighted_quality_score(fragments)
        total_effective = sum(f.get('effective_duration', 0) for f in fragments)
        time_coeff = calculate_time_coefficient(total_effective)
        signal_coeff = calculate_signal_gain_coefficient(signals, rebellion_score)
        
        flow_score = calculate_flow_index(weighted_quality * signal_coeff, time_coeff)
        level, icon = get_flow_level(flow_score)
        
        return {
            'flow_score': flow_score,
            'level': level,
            'icon': icon,
            'weighted_quality': weighted_quality,
            'time_coefficient': time_coeff,
            'signal_coefficient': signal_coeff
        }
    
    def analyze_fragment(self, fragment: dict) -> dict:
        """分析单个心流片段"""
        interruptions = fragment.get('interruptions', [])
        effective_duration = calculate_effective_duration(
            fragment.get('duration_min', 0), 
            interruptions
        )
        
        dimensions = fragment.get('dimensions', [0.5, 0.5, 0.5])
        quality_score = calculate_base_quality_score(dimensions)
        
        return {
            'effective_duration': effective_duration,
            'quality_score': quality_score,
            'interruption_count': len(interruptions)
        }