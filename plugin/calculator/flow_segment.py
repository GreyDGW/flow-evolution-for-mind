"""Segment effective-time calculation (PRD 4.1)."""

from .flow_models import FlowSegment

MICRO_INTERRUPTION_PENALTY_MINUTES = 3.0
WARMUP_DEDUCTION_MINUTES = 15.0


def calculate_segment_effective_minutes(segment: FlowSegment) -> float:
    """
    PRD rule:
    片段有效时长 = max(原始时长 - 中断惩罚 - 预热扣除, 0)
    """
    interruption_penalty = 0.0
    warmup_deduction = 0.0

    if segment.interruption_type == "micro":
        interruption_penalty = MICRO_INTERRUPTION_PENALTY_MINUTES
    elif segment.interruption_type in {"medium", "major"}:
        warmup_deduction = WARMUP_DEDUCTION_MINUTES

    return max(segment.duration_minutes - interruption_penalty - warmup_deduction, 0.0)


def calculate_total_effective_minutes(segments: list[FlowSegment]) -> float:
    """Sum effective minutes for all segments."""
    return sum(calculate_segment_effective_minutes(s) for s in segments)


class FlowSegmenter:
    """心流片段分割器"""
    
    def __init__(self):
        self.segments = []
    
    def add_segment(self, duration_minutes: float, interruption_type: str = "micro"):
        """添加心流片段"""
        segment = FlowSegment(
            duration_minutes=duration_minutes,
            interruption_type=interruption_type
        )
        self.segments.append(segment)
    
    def get_segments(self) -> list[FlowSegment]:
        """获取所有片段"""
        return self.segments
    
    def calculate_total_effective(self) -> float:
        """计算总有效时长"""
        return calculate_total_effective_minutes(self.segments)
    
    def clear(self):
        """清空所有片段"""
        self.segments = []