import pytest

from openclaw_flow_plugin.core.flow_index import calculate_flow_base_quality
from openclaw_flow_plugin.core.flow_models import FlowQualityInput
from openclaw_flow_plugin.core.flow_quality import calculate_base_quality_score


def test_base_quality_min_value():
    quality = FlowQualityInput(
        logic_depth=0,
        orderliness=0,
        progressiveness=0,
        judgment_vector=0,
        goal_alignment=0,
    )
    assert calculate_base_quality_score(quality) == 0.0


def test_base_quality_max_value():
    quality = FlowQualityInput(
        logic_depth=3,
        orderliness=3,
        progressiveness=3,
        judgment_vector=3,
        goal_alignment=3,
    )
    assert calculate_base_quality_score(quality) == 1.0


def test_base_quality_mixed_value():
    quality = FlowQualityInput(
        logic_depth=3,
        orderliness=2,
        progressiveness=1,
        judgment_vector=0,
        goal_alignment=3,
    )
    # ((3+2+1+0+3) * 0.2) / 3 = 0.6
    assert calculate_flow_base_quality(quality) == 0.6


def test_base_quality_invalid_dimension_raises():
    quality = FlowQualityInput(
        logic_depth=4,
        orderliness=2,
        progressiveness=1,
        judgment_vector=0,
        goal_alignment=3,
    )
    with pytest.raises(ValueError):
        calculate_base_quality_score(quality)

