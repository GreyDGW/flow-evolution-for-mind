"""Base quality score calculation (PRD 4.2)."""

from .flow_models import FlowQualityInput

WEIGHT = 0.20
MAX_DIMENSION_SCORE = 3.0


def _validate_dimension_score(value: int, name: str) -> None:
    if value < 0 or value > 3:
        raise ValueError(f"{name} must be in [0, 3], got {value}")


def calculate_base_quality_score(quality: FlowQualityInput) -> float:
    """
    PRD formula:
    基础质量分 = Σ(维度得分_i × 0.20) / 3

    Return range: [0, 1.0]
    """
    _validate_dimension_score(quality.logic_depth, "logic_depth")
    _validate_dimension_score(quality.orderliness, "orderliness")
    _validate_dimension_score(quality.progressiveness, "progressiveness")
    _validate_dimension_score(quality.judgment_vector, "judgment_vector")
    _validate_dimension_score(quality.goal_alignment, "goal_alignment")

    weighted_sum = (
        quality.logic_depth * WEIGHT
        + quality.orderliness * WEIGHT
        + quality.progressiveness * WEIGHT
        + quality.judgment_vector * WEIGHT
        + quality.goal_alignment * WEIGHT
    )
    return weighted_sum / MAX_DIMENSION_SCORE


class FlowQualityAnalyzer:
    """心流质量分析器"""
    
    def __init__(self):
        pass
    
    def analyze(self, text: str) -> FlowQualityInput:
        """分析文本内容，计算质量维度得分"""
        logic_depth = self._calculate_logic_depth(text)
        orderliness = self._calculate_orderliness(text)
        progressiveness = self._calculate_progressiveness(text)
        judgment_vector = self._calculate_judgment_vector(text)
        goal_alignment = self._calculate_goal_alignment(text)
        
        return FlowQualityInput(
            logic_depth=logic_depth,
            orderliness=orderliness,
            progressiveness=progressiveness,
            judgment_vector=judgment_vector,
            goal_alignment=goal_alignment
        )
    
    def _calculate_logic_depth(self, text: str) -> int:
        """计算逻辑深度"""
        depth = 0
        if '因为' in text or '所以' in text or '因此' in text:
            depth += 1
        if '首先' in text or '其次' in text or '最后' in text:
            depth += 1
        if '分析' in text or '推理' in text or '论证' in text:
            depth += 1
        return min(depth, 3)
    
    def _calculate_orderliness(self, text: str) -> int:
        """计算条理性"""
        order = 0
        if len(text) > 50:
            order += 1
        if '。' in text or '！' in text or '？' in text:
            order += 1
        if '一、' in text or '二、' in text or '1.' in text:
            order += 1
        return min(order, 3)
    
    def _calculate_progressiveness(self, text: str) -> int:
        """计算递进性"""
        progress = 0
        if '但是' in text or '然而' in text:
            progress += 1
        if '不仅' in text or '而且' in text:
            progress += 1
        if '进一步' in text or '深入' in text:
            progress += 1
        return min(progress, 3)
    
    def _calculate_judgment_vector(self, text: str) -> int:
        """计算判断向量"""
        judgment = 0
        if '认为' in text or '觉得' in text:
            judgment += 1
        if '应该' in text or '建议' in text:
            judgment += 1
        if '必须' in text or '需要' in text:
            judgment += 1
        return min(judgment, 3)
    
    def _calculate_goal_alignment(self, text: str) -> int:
        """计算目标对齐度"""
        alignment = 0
        if '目标' in text or '目的' in text:
            alignment += 1
        if '完成' in text or '达成' in text:
            alignment += 1
        if '结果' in text or '效果' in text:
            alignment += 1
        return min(alignment, 3)