"""Plugin entrypoint placeholder for OpenClaw integration."""

from openclaw_flow_plugin.core.achievement import calculate_achievement_result
from openclaw_flow_plugin.core.bio_guard import evaluate_bio_guard
from openclaw_flow_plugin.core.cognitive_evolution import calculate_cognitive_evolution_index
from openclaw_flow_plugin.core.ewci import calculate_ewci
from openclaw_flow_plugin.core.models import CoreInputs, FullPluginInputs
from openclaw_flow_plugin.core.strategic_index import calculate_strategic_index


def run_plugin(inputs: CoreInputs) -> dict:
    """
    Minimal plugin entrypoint.

    Later this function can be wired into real OpenClaw hooks.
    """
    strategic = calculate_strategic_index(inputs)
    return {
        "strategic_index": strategic.strategic_index,
        "power": strategic.power,
        "navigation_raw": strategic.navigation_raw,
        "navigation_percent": strategic.navigation_percent,
        "navigation_state": strategic.navigation_state,
    }


def run_full_plugin(inputs: FullPluginInputs) -> dict:
    """
    Full v1 scaffold pipeline from PRD chapters 1/2/3/5/6.

    Flow index is expected to be pre-calculated by the flow module and passed in
    `inputs.core.flow_index`.
    """
    achievement = calculate_achievement_result(
        short_term=inputs.achievement.short_term_score,
        mid_term=inputs.achievement.mid_term_score,
        long_term=inputs.achievement.long_term_score,
        drift_minutes=inputs.achievement.drift_minutes,
        focus_minutes=inputs.achievement.focus_minutes,
    )
    ewci = calculate_ewci(
        total_period_minutes=inputs.ewci.total_period_minutes,
        active_work_minutes=inputs.ewci.active_work_minutes,
        closed_loops=inputs.ewci.closed_loops,
        average_output_coefficient=inputs.ewci.average_output_coefficient,
        average_completeness=inputs.ewci.average_completeness,
    )
    bio = evaluate_bio_guard(
        recent_three_days_strategic_scores=inputs.bio.recent_three_days_strategic_scores,
        has_late_night_activity=inputs.bio.has_late_night_activity,
        recent_three_days_flow_scores=inputs.bio.recent_three_days_flow_scores,
        user_days_since_start=inputs.bio.user_days_since_start,
    )
    cognitive = calculate_cognitive_evolution_index(
        logic_chain=inputs.cognitive.logic_chain,
        concept_density=inputs.cognitive.concept_density,
        causal_depth=inputs.cognitive.causal_depth,
        self_correction=inputs.cognitive.self_correction,
        cross_domain_links=inputs.cognitive.cross_domain_links,
        current_week_hub_stability=inputs.cognitive.current_week_hub_stability,
        previous_week_hub_stability=inputs.cognitive.previous_week_hub_stability,
        high_quality_minutes=inputs.cognitive.high_quality_minutes,
        is_t0_observation_window=inputs.cognitive.is_t0_observation_window,
    )

    strategic = calculate_strategic_index(
        CoreInputs(
            flow_index=inputs.core.flow_index,
            cognitive_evolution_index=cognitive.cognitive_evolution_index,
            ewci=ewci.ewci,
            achievement_fit=achievement.achievement_fit,
            drift_rate=achievement.drift_rate if achievement.drift_rate is not None else 0.0,
        )
    )

    return {
        "achievement_fit": achievement.achievement_fit,
        "drift_rate": achievement.drift_rate,
        "ewci": ewci.ewci,
        "cognitive_evolution_index": cognitive.cognitive_evolution_index,
        "strategic_index": strategic.strategic_index,
        "power": strategic.power,
        "navigation_raw": strategic.navigation_raw,
        "navigation_percent": strategic.navigation_percent,
        "navigation_state": strategic.navigation_state,
        "fatigue_guard_triggered": bio.fatigue_guard_triggered,
        "fatigue_guard_reason": bio.fatigue_guard_reason,
        "is_t0_window": bio.is_t0_window,
    }

