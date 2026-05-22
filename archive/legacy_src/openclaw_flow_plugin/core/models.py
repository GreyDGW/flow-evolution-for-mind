"""Data models for core algorithm inputs/outputs."""

from dataclasses import dataclass


@dataclass
class CoreInputs:
    """Inputs needed by chapter 1 core algorithm."""

    flow_index: float
    cognitive_evolution_index: float
    ewci: float
    achievement_fit: float
    drift_rate: float


@dataclass
class StrategicIndexResult:
    """Output of the strategic (gated) index calculation."""

    strategic_index: float
    power: float
    navigation_raw: float
    navigation_percent: float
    navigation_state: str


@dataclass
class AchievementFitInputs:
    short_term_score: float
    mid_term_score: float
    long_term_score: float
    drift_minutes: float
    focus_minutes: float


@dataclass
class EwciInputs:
    total_period_minutes: float
    active_work_minutes: float
    closed_loops: int
    average_output_coefficient: float
    average_completeness: float


@dataclass
class CognitiveEvolutionInputs:
    logic_chain: int
    concept_density: int
    causal_depth: int
    self_correction: int
    cross_domain_links: int
    current_week_hub_stability: float
    previous_week_hub_stability: float
    high_quality_minutes: float
    is_t0_observation_window: bool = False


@dataclass
class BioGuardInputs:
    recent_three_days_strategic_scores: list[float]
    has_late_night_activity: bool
    recent_three_days_flow_scores: list[float]
    user_days_since_start: int


@dataclass
class FullPluginInputs:
    core: CoreInputs
    achievement: AchievementFitInputs
    ewci: EwciInputs
    cognitive: CognitiveEvolutionInputs
    bio: BioGuardInputs

