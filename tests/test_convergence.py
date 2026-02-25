"""
Jyotish AI — Test Convergence Scoring

Validates the weighted convergence computation and confidence level mapping.
"""

from jyotish_ai.domain.types import ConfidenceLevel
from jyotish_ai.domain.models import GateResult
from jyotish_ai.prediction.convergence import compute_convergence


def _make_gate(score: float, is_sufficient: bool = True) -> GateResult:
    """Helper to create a minimal GateResult with given score and sufficiency."""
    return GateResult(
        gate_name="test_gate",
        score=score,
        is_sufficient=is_sufficient,
        details={},
    )


def test_high_confidence_scores():
    """Scores of 0.9 each with default weights (1.0) should yield convergence >= 2.5 -> HIGH."""
    gate1 = _make_gate(0.9)
    gate2 = _make_gate(0.9)
    gate3 = _make_gate(0.9)
    score, level = compute_convergence(gate1, gate2, gate3)
    assert score >= 2.5
    assert level == ConfidenceLevel.HIGH


def test_medium_confidence_scores():
    """Scores of 0.6 each -> convergence ~1.8 -> MEDIUM."""
    gate1 = _make_gate(0.6)
    gate2 = _make_gate(0.6)
    gate3 = _make_gate(0.6)
    score, level = compute_convergence(gate1, gate2, gate3)
    assert 1.5 <= score < 2.5
    assert level == ConfidenceLevel.MEDIUM


def test_low_confidence_scores():
    """Scores of 0.2 each -> convergence ~0.6 -> LOW."""
    gate1 = _make_gate(0.2)
    gate2 = _make_gate(0.2)
    gate3 = _make_gate(0.2)
    score, level = compute_convergence(gate1, gate2, gate3)
    assert 0.5 <= score < 1.5
    assert level == ConfidenceLevel.LOW


def test_negative_confidence_scores():
    """Scores of 0.1 each -> convergence ~0.3 -> NEGATIVE."""
    gate1 = _make_gate(0.1)
    gate2 = _make_gate(0.1)
    gate3 = _make_gate(0.1)
    score, level = compute_convergence(gate1, gate2, gate3)
    assert score < 0.5
    assert level == ConfidenceLevel.NEGATIVE


def test_insufficient_when_gate1_not_sufficient():
    """When gate1.is_sufficient is False, result should be INSUFFICIENT regardless of scores."""
    gate1 = _make_gate(0.9, is_sufficient=False)
    gate2 = _make_gate(0.9)
    gate3 = _make_gate(0.9)
    score, level = compute_convergence(gate1, gate2, gate3)
    assert score == 0.0
    assert level == ConfidenceLevel.INSUFFICIENT
