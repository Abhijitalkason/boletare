"""
Jyotish AI — Layer 2: Convergence Scoring

Combines gate scores into a weighted sum and maps to confidence levels.
Architecture doc: score = w1*G1 + w2*G2 + w3*G3 (max 3.0)
"""

from __future__ import annotations
from jyotish_ai.domain.types import ConfidenceLevel
from jyotish_ai.domain.models import GateResult


def compute_convergence(
    gate1: GateResult,
    gate2: GateResult,
    gate3: GateResult,
    w1: float = 1.0,
    w2: float = 1.0,
    w3: float = 1.0,
) -> tuple[float, ConfidenceLevel]:
    """Compute weighted convergence score and confidence level.

    Args:
        gate1-3: Results from the three gates
        w1-w3: Gate weights (default 1.0 each, max sum = 3.0)

    Returns:
        (convergence_score, confidence_level)

    Thresholds:
        >= 2.5 → HIGH
        >= 1.5 → MEDIUM
        >= 0.5 → LOW
        < 0.5  → NEGATIVE

    Special case: if gate1.is_sufficient is False → INSUFFICIENT
    """
    if not gate1.is_sufficient:
        return 0.0, ConfidenceLevel.INSUFFICIENT

    score = w1 * gate1.score + w2 * gate2.score + w3 * gate3.score

    if score >= 2.5:
        level = ConfidenceLevel.HIGH
    elif score >= 1.5:
        level = ConfidenceLevel.MEDIUM
    elif score >= 0.5:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.NEGATIVE

    return round(score, 4), level
