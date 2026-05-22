def calculate_power(flow_index: float, cognitive_evolution: float, ewci: float) -> float:
    return flow_index * 0.35 + cognitive_evolution * 0.25 + ewci * 0.40


class PowerCalculator:
    """动力计算器"""
    
    def __init__(self):
        pass
    
    def calculate(self, flow_index: float, cognitive_evolution: float, ewci: float) -> float:
        """计算动力指数"""
        return calculate_power(flow_index, cognitive_evolution, ewci)