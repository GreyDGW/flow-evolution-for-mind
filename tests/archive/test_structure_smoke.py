"""Smoke test for scaffold imports."""

from openclaw_flow_plugin.core.models import CoreInputs
from openclaw_flow_plugin.plugin import run_plugin


def test_scaffold_runs():
    inputs = CoreInputs(
        flow_index=70.0,
        cognitive_evolution_index=65.0,
        ewci=80.0,
        achievement_fit=75.0,
        drift_rate=20.0,
    )
    result = run_plugin(inputs)
    assert "strategic_index" in result
    assert "power" in result

