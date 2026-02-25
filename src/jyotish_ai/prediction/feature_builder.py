"""
Jyotish AI — Layer 2: Feature Vector Builder

Constructs a 22-dimensional feature vector from prediction components.
All features normalized to [0, 1] for XGBoost calibration (Phase 3).

Feature layout:
  0-4:   Gate 1 sub-scores (promise, lord_dignity, occupants, navamsha, sav)
  5-8:   Gate 2 sub-scores (dasha, md, ad, connection_count_normalized)
  9-11:  Gate 3 sub-scores (transit, active_months_ratio, peak_bav)
  12:    convergence_score (divided by 3.0 to normalize)
  13-17: quality flags (tier, lagna_mode, boundary, ambiguous, retrospective)
  18-21: demographics (gender, age, education, income) — all 0.5 placeholder for Phase 1
"""

from __future__ import annotations
from jyotish_ai.domain.types import BirthTimeTier, LagnaMode
from jyotish_ai.domain.models import GateResult, QualityFlags


def build_feature_vector(
    gate1: GateResult,
    gate2: GateResult,
    gate3: GateResult,
    convergence_score: float,
    quality_flags: QualityFlags,
) -> list[float]:
    """Build a 22-dimensional feature vector from prediction components.

    All values are normalized to [0.0, 1.0].

    Args:
        gate1-3: Gate results with details dicts containing sub-scores
        convergence_score: Weighted sum (0-3)
        quality_flags: Quality metadata

    Returns:
        List of 22 floats, each in [0.0, 1.0]
    """
    features: list[float] = []

    # Features 0-4: Gate 1 sub-scores
    g1d = gate1.details
    features.append(_clamp(g1d.get("lord_dignity", 0.0)))           # 0
    features.append(_clamp(g1d.get("occupant_score", 0.5)))         # 1
    features.append(_clamp(g1d.get("navamsha_score", 0.0)))         # 2
    features.append(_clamp(g1d.get("sav_normalized", 0.0)))         # 3
    features.append(_clamp(gate1.score))                             # 4

    # Features 5-8: Gate 2 sub-scores
    g2d = gate2.details
    features.append(_clamp(g2d.get("md_score", 0.0)))               # 5
    features.append(_clamp(g2d.get("ad_score", 0.0)))               # 6
    features.append(_clamp(gate2.score))                             # 7
    # Connection count normalized: md has 4 possible + ad has 4 possible = 8 max
    md_conns = sum(1 for v in g2d.get("md_connections", {}).values() if v)
    ad_conns = sum(1 for v in g2d.get("ad_connections", {}).values() if v)
    features.append(_clamp((md_conns + ad_conns) / 8.0))            # 8

    # Features 9-11: Gate 3 sub-scores
    g3d = gate3.details
    features.append(_clamp(gate3.score))                             # 9
    total_months = g3d.get("total_months", 24)
    active = g3d.get("active_months_count", 0)
    features.append(_clamp(active / max(total_months, 1)))           # 10
    features.append(_clamp(g3d.get("peak_bav_score", 0.0)))         # 11

    # Feature 12: convergence score (normalize 0-3 to 0-1)
    features.append(_clamp(convergence_score / 3.0))                 # 12

    # Features 13-17: quality flags
    # Tier: 1→1.0, 2→0.5, 3→0.0
    tier_map = {BirthTimeTier.TIER_1: 1.0, BirthTimeTier.TIER_2: 0.5, BirthTimeTier.TIER_3: 0.0}
    features.append(tier_map.get(quality_flags.birth_time_tier, 0.5))  # 13
    features.append(1.0 if quality_flags.lagna_mode == LagnaMode.CHANDRA else 0.0)  # 14
    features.append(1.0 if quality_flags.dasha_boundary_sensitive else 0.0)  # 15
    features.append(1.0 if quality_flags.dasha_ambiguous else 0.0)  # 16
    features.append(1.0 if quality_flags.is_retrospective else 0.0) # 17

    # Features 18-21: demographics (placeholder 0.5 for Phase 1)
    features.extend([0.5, 0.5, 0.5, 0.5])  # 18-21

    assert len(features) == 22, f"Expected 22 features, got {len(features)}"
    return features


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))
