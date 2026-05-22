from openclaw_flow_plugin.core.achievement import calculate_achievement_result
from openclaw_flow_plugin.core.bio_guard import evaluate_bio_guard
from openclaw_flow_plugin.core.cognitive_evolution import calculate_cognitive_evolution_index
from openclaw_flow_plugin.core.ewci import calculate_ewci


def test_achievement_and_drift():
    result = calculate_achievement_result(80, 70, 90, drift_minutes=30, focus_minutes=90)
    assert result.achievement_fit == 81.0
    assert result.drift_rate == 25.0


def test_ewci_closed_loops_zero():
    result = calculate_ewci(540, 300, 0, 0.8, 70)
    assert result.ewci == 0.0


def test_cognitive_evolution_index_bounds():
    result = calculate_cognitive_evolution_index(3, 3, 3, 3, 3, 1.0, 0.5, 120, False)
    assert 0.0 <= result.cognitive_evolution_index <= 100.0


def test_bio_guard_trigger():
    result = evaluate_bio_guard(
        recent_three_days_strategic_scores=[80, 82, 78],
        has_late_night_activity=True,
        recent_three_days_flow_scores=[75, 70, 60],
        user_days_since_start=3,
    )
    assert result.fatigue_guard_triggered is True
    assert result.is_t0_window is True

