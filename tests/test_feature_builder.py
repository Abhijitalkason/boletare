"""
Jyotish AI — Test Feature Vector Builder

Validates the 22-dimensional feature vector construction from prediction components.
"""

from jyotish_ai.domain.types import BirthTimeTier, LagnaMode
from jyotish_ai.domain.models import GateResult, QualityFlags
from jyotish_ai.prediction.feature_builder import build_feature_vector


def _make_gate(score: float, details: dict) -> GateResult:
    """Helper to create a GateResult with given score and details."""
    return GateResult(
        gate_name="test_gate",
        score=score,
        is_sufficient=True,
        details=details,
    )


def _make_gates_and_flags():
    """Helper to build a complete set of gates and quality flags for testing."""
    gate1 = _make_gate(0.6, {
        "lord_dignity": 0.5,
        "occupant_score": 0.5,
        "navamsha_score": 0.8,
        "sav_normalized": 0.6,
    })
    gate2 = _make_gate(0.5, {
        "md_score": 0.4,
        "ad_score": 0.3,
        "md_connections": {"is_event_lord": True, "placed_in_house": False,
                           "aspects_house": False, "connected_to_lord": False},
        "ad_connections": {"is_event_lord": False, "placed_in_house": False,
                           "aspects_house": True, "connected_to_lord": False},
    })
    gate3 = _make_gate(0.4, {
        "total_months": 24,
        "active_months_count": 6,
        "peak_bav_score": 0.7,
    })
    qf = QualityFlags(birth_time_tier=BirthTimeTier.TIER_2)
    return gate1, gate2, gate3, qf


def test_vector_length_is_22():
    """Feature vector should be exactly 22 elements long."""
    gate1, gate2, gate3, qf = _make_gates_and_flags()
    vec = build_feature_vector(gate1, gate2, gate3, 1.5, qf)
    assert len(vec) == 22


def test_all_values_in_0_to_1():
    """Every element of the feature vector should be in [0.0, 1.0]."""
    gate1, gate2, gate3, qf = _make_gates_and_flags()
    vec = build_feature_vector(gate1, gate2, gate3, 1.5, qf)
    for i, val in enumerate(vec):
        assert 0.0 <= val <= 1.0, f"Feature[{i}] = {val} is out of range [0.0, 1.0]"


def test_demographic_placeholders_are_0_5():
    """Features 18-21 (demographics) should all be 0.5 as Phase 1 placeholders."""
    gate1, gate2, gate3, qf = _make_gates_and_flags()
    vec = build_feature_vector(gate1, gate2, gate3, 1.5, qf)
    for i in range(18, 22):
        assert vec[i] == 0.5, f"Feature[{i}] = {vec[i]}, expected 0.5 (demographic placeholder)"
