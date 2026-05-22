from openclaw_flow_plugin.core.flow_index import calculate_flow_time_factor_from_segments
from openclaw_flow_plugin.core.flow_models import FlowSegment
from openclaw_flow_plugin.core.flow_segment import calculate_total_effective_minutes
from openclaw_flow_plugin.core.flow_time_factor import calculate_time_factor


def test_effective_minutes_micro_interruptions():
    segments = [
        FlowSegment(duration_minutes=30, interruption_type="micro"),
        FlowSegment(duration_minutes=20, interruption_type="micro"),
    ]
    # 30-3 + 20-3 = 44
    assert calculate_total_effective_minutes(segments) == 44


def test_effective_minutes_medium_interruptions():
    segments = [FlowSegment(duration_minutes=40, interruption_type="medium")]
    # 40-15 = 25
    assert calculate_total_effective_minutes(segments) == 25


def test_time_factor_bounds():
    assert calculate_time_factor(0) == 0.0
    assert calculate_time_factor(10000) == 1.0


def test_flow_time_factor_from_segments():
    segments = [
        FlowSegment(duration_minutes=60, interruption_type="micro"),
        FlowSegment(duration_minutes=30, interruption_type="medium"),
    ]
    factor = calculate_flow_time_factor_from_segments(segments)
    assert 0.0 < factor <= 1.0

