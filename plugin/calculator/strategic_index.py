from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategicIndexResult:
    power: float
    goal_alignment: float
    goal_alignment_percent: float
    strategic_index: float
    strategic_level: str
    strategic_icon: str


@dataclass
class CoreInputs:
    flow_index: float
    cognitive_evolution_index: float
    ewci: float
    achievement_fit: float
    drift_rate: float
    cognitive_growth_level: str = "中"


def calculate_power(flow_index: float, cognitive_evolution: float, ewci: float) -> float:
    return flow_index * 0.35 + cognitive_evolution * 0.25 + ewci * 0.40


def get_exploration_exemption(cognitive_level: str) -> float:
    exemptions = {"高": 0.5, "中": 0.8, "低": 1.0, "危": 1.0}
    return exemptions.get(cognitive_level, 1.0)


def calculate_goal_alignment(achievement_fit: float, drift_rate: float, cognitive_level: str) -> float:
    exemption = get_exploration_exemption(cognitive_level)
    return (achievement_fit / 100 * (1 - drift_rate / 100 * exemption) * 2) - 1


def goal_alignment_to_percent(alignment: float) -> float:
    return (alignment + 1) * 50


def get_strategic_level(score: float) -> tuple:
    if score >= 75:
        return ("卓越", "🎯")
    elif score >= 50:
        return ("达成", "✅")
    elif score >= 25:
        return ("偏离", "⚠️")
    else:
        return ("失效", "❌")


def calculate_strategic_index(inputs: CoreInputs) -> StrategicIndexResult:
    power = calculate_power(inputs.flow_index, inputs.cognitive_evolution_index, inputs.ewci)
    alignment = calculate_goal_alignment(inputs.achievement_fit, inputs.drift_rate, inputs.cognitive_growth_level)
    alignment_percent = goal_alignment_to_percent(alignment)
    
    if alignment_percent > 50:
        strategic = power * (alignment_percent / 100)
    else:
        strategic = power * max(alignment_percent / 100, 0.05)
    
    level, icon = get_strategic_level(strategic)
    
    return StrategicIndexResult(
        power=power,
        goal_alignment=alignment,
        goal_alignment_percent=alignment_percent,
        strategic_index=strategic,
        strategic_level=level,
        strategic_icon=icon
    )


class StrategicIndexCalculator:
    """战略指数计算器"""
    
    def __init__(self):
        pass
    
    def calculate(self, flow_index: float, cognitive_evolution: float, ewci: float,
                  achievement_fit: float, drift_rate: float, cognitive_level: str = "中") -> StrategicIndexResult:
        """计算战略指数"""
        inputs = CoreInputs(
            flow_index=flow_index,
            cognitive_evolution_index=cognitive_evolution,
            ewci=ewci,
            achievement_fit=achievement_fit,
            drift_rate=drift_rate,
            cognitive_growth_level=cognitive_level
        )
        return calculate_strategic_index(inputs)