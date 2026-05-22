"""Data models for flow index calculation."""

from dataclasses import dataclass
from typing import Literal, Optional

InterruptionType = Literal["micro", "medium", "major"]


@dataclass
class FlowState:
    """心流状态模型"""
    
    is_in_flow: bool = False
    flow_score: float = 0.0
    quality_level: str = "low"
    interruption_count: int = 0
    effective_duration_min: float = 0.0
    last_interruption_time: Optional[float] = None


@dataclass
class FlowQuality:
    """心流质量评估模型"""
    
    logic_depth: int = 0
    orderliness: int = 0
    progressiveness: int = 0
    judgment_vector: int = 0
    goal_alignment: int = 0
    
    def calculate_score(self) -> float:
        """计算综合质量分数"""
        total = self.logic_depth + self.orderliness + self.progressiveness + \
                self.judgment_vector + self.goal_alignment
        return total / 15.0


@dataclass
class FlowSegment:
    """
    One active-work segment between major interruptions.

    - duration_minutes: raw segment duration
    - interruption_type:
      - micro  => -3 min penalty, keep segment
      - medium => segment end, warmup deduction
      - major  => segment end, warmup deduction, high-risk mark
    """

    duration_minutes: float
    interruption_type: InterruptionType = "micro"


@dataclass
class FlowQualityInput:
    """
    PRD 4.2 base-quality dimensions (each score in 0-3).
    """

    logic_depth: int
    orderliness: int
    progressiveness: int
    judgment_vector: int
    goal_alignment: int


@dataclass
class FlowSignalInput:
    """
    PRD 4.3 signal dimensions (each score in 0-3).
    """

    rebellion: int
    followup: int
    correction: int
    time_depth: int
    meta_cognition: int


@dataclass
class FlowSlice:
    """
    A slice combines one work segment + quality/signal scoring.
    """

    segment: FlowSegment
    quality: FlowQualityInput
    signal: FlowSignalInput


@dataclass
class FlowIndexResult:
    """Daily flow index output for plugin usage."""

    daily_flow_index: float
    weighted_quality_score: float
    time_factor: float
    total_effective_minutes: float
    major_interruptions: int