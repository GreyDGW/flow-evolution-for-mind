from typing import Tuple, List


def calculate_daily_structure_score(dimensions: List[float]) -> float:
    return sum(dimensions) / len(dimensions) * 100 / 3


def calculate_stability_coefficient(this_week_stability: float, last_week_stability: float) -> float:
    change = this_week_stability - last_week_stability
    return 1 + change * 0.5


def get_rhythm_coefficient(rhythm_type: str) -> float:
    coefficients = {
        "输入期": 1.1,
        "混沌期": 1.1,
        "沉淀期": 1.1,
        "顿悟期": 1.35,
        "平台期": 0.7
    }
    return coefficients.get(rhythm_type, 1.0)


def calculate_cognitive_growth(
    daily_structure: float,
    stability_coeff: float,
    rhythm_coeff: float,
    high_quality_duration_min: float
) -> float:
    base = daily_structure * stability_coeff * rhythm_coeff
    if high_quality_duration_min <= 180:
        base *= 1.5
    return min(base, 100)


def get_cognitive_level(score: float) -> Tuple[str, str]:
    if score >= 75:
        return ("高", "🟢")
    elif score >= 50:
        return ("中", "🟡")
    elif score >= 25:
        return ("低", "🟠")
    else:
        return ("危", "🔴")


class CognitiveEvolutionAnalyzer:
    """认知进化分析器"""
    
    def __init__(self):
        pass
    
    def analyze(self, daily_structure: float, stability: float, last_week_stability: float,
                rhythm_type: str, high_quality_duration: float) -> dict:
        """分析认知进化状态"""
        stability_coeff = calculate_stability_coefficient(stability, last_week_stability)
        rhythm_coeff = get_rhythm_coefficient(rhythm_type)
        growth_score = calculate_cognitive_growth(daily_structure, stability_coeff, 
                                                  rhythm_coeff, high_quality_duration)
        level, icon = get_cognitive_level(growth_score)
        
        return {
            'growth_score': growth_score,
            'level': level,
            'icon': icon,
            'stability_coeff': stability_coeff,
            'rhythm_coeff': rhythm_coeff
        }
    
    def get_rhythm_type(self, analysis_data: dict) -> str:
        """根据分析数据判断节奏类型"""
        if analysis_data.get('insight_count', 0) > 3:
            return "顿悟期"
        elif analysis_data.get('confusion_level', 0) > 0.7:
            return "混沌期"
        elif analysis_data.get('input_count', 0) > 10:
            return "输入期"
        elif analysis_data.get('stability', 0) > 0.8:
            return "沉淀期"
        else:
            return "平台期"