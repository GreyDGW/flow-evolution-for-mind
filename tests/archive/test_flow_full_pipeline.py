from openclaw_flow_plugin.core.flow_index import calculate_daily_flow_index
from openclaw_flow_plugin.core.flow_models import FlowQualityInput, FlowSegment, FlowSignalInput, FlowSlice


def _quality(v: int) -> FlowQualityInput:
    return FlowQualityInput(v, v, v, v, v)


def _signal(v: int) -> FlowSignalInput:
    return FlowSignalInput(v, v, v, v, v)


def test_daily_flow_index_basic():
    slices = [
        FlowSlice(
            segment=FlowSegment(duration_minutes=60, interruption_type="micro"),
            quality=_quality(2),
            signal=_signal(2),
        ),
        FlowSlice(
            segment=FlowSegment(duration_minutes=40, interruption_type="medium"),
            quality=_quality(3),
            signal=_signal(3),
        ),
    ]
    result = calculate_daily_flow_index(slices)
    assert 0.0 <= result.daily_flow_index <= 100.0
    assert result.total_effective_minutes > 0


def test_daily_flow_index_interrupt_penalty():
    slices = [
        FlowSlice(FlowSegment(30, "major"), _quality(3), _signal(3)),
        FlowSlice(FlowSegment(30, "major"), _quality(3), _signal(3)),
        FlowSlice(FlowSegment(30, "major"), _quality(3), _signal(3)),
    ]
    result = calculate_daily_flow_index(slices)
    assert result.major_interruptions == 3
    assert result.daily_flow_index <= result.weighted_quality_score

