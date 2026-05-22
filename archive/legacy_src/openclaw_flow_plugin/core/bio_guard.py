"""Biological guardrails (PRD chapter 6)."""

from dataclasses import dataclass


@dataclass
class BioGuardResult:
    fatigue_guard_triggered: bool
    fatigue_guard_reason: str
    is_t0_window: bool


def evaluate_fatigue_guard(
    recent_three_days_strategic_scores: list[float],
    has_late_night_activity: bool,
    recent_three_days_flow_scores: list[float],
) -> tuple[bool, str]:
    """
    Trigger when all hold:
    1) 3-day strategic >= 75
    2) late-night activity exists
    3) flow trend down (day3 < day1)
    """
    if len(recent_three_days_strategic_scores) < 3 or len(recent_three_days_flow_scores) < 3:
        return False, "insufficient_data"

    cond1 = all(score >= 75 for score in recent_three_days_strategic_scores[-3:])
    cond2 = has_late_night_activity
    flow = recent_three_days_flow_scores[-3:]
    cond3 = flow[2] < flow[0]
    triggered = cond1 and cond2 and cond3
    return triggered, "fatigue_guard_triggered" if triggered else "normal"


def evaluate_bio_guard(
    recent_three_days_strategic_scores: list[float],
    has_late_night_activity: bool,
    recent_three_days_flow_scores: list[float],
    user_days_since_start: int,
) -> BioGuardResult:
    triggered, reason = evaluate_fatigue_guard(
        recent_three_days_strategic_scores, has_late_night_activity, recent_three_days_flow_scores
    )
    return BioGuardResult(
        fatigue_guard_triggered=triggered,
        fatigue_guard_reason=reason,
        is_t0_window=user_days_since_start <= 7,
    )


class BioGuard:
    """生物防护系统"""
    
    def __init__(self):
        pass
    
    def evaluate_fatigue(self, recent_three_days_strategic_scores: list[float],
                         has_late_night_activity: bool,
                         recent_three_days_flow_scores: list[float]) -> tuple[bool, str]:
        """评估疲劳防护"""
        return evaluate_fatigue_guard(recent_three_days_strategic_scores, 
                                       has_late_night_activity, 
                                       recent_three_days_flow_scores)
    
    def evaluate(self, recent_three_days_strategic_scores: list[float],
                 has_late_night_activity: bool,
                 recent_three_days_flow_scores: list[float],
                 user_days_since_start: int) -> BioGuardResult:
        """评估生物防护"""
        return evaluate_bio_guard(recent_three_days_strategic_scores,
                                   has_late_night_activity,
                                   recent_three_days_flow_scores,
                                   user_days_since_start)