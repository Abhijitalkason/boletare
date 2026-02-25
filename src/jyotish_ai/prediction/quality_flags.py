"""
Jyotish AI — Layer 2: Quality Flag Computation

Assembles quality metadata from the birth chart and prediction context.
"""

from __future__ import annotations
from jyotish_ai.domain.types import BirthTimeTier, LagnaMode
from jyotish_ai.domain.models import BirthChart, QualityFlags


def compute_quality_flags(
    chart: BirthChart,
    is_retrospective: bool = False,
) -> QualityFlags:
    """Compute quality flags from chart metadata and prediction context.

    The chart already carries boundary/quality info from Layer 1.
    This function combines it with prediction-level context (retrospective flag).

    Args:
        chart: Complete birth chart with quality_flags already populated
        is_retrospective: Whether this prediction is for a past event

    Returns:
        QualityFlags with all fields populated
    """
    return QualityFlags(
        birth_time_tier=chart.quality_flags.birth_time_tier,
        lagna_mode=chart.lagna_mode,
        dasha_boundary_sensitive=chart.boundary_flags.dasha_boundary_sensitive,
        dasha_ambiguous=chart.dasha_tree_alt is not None,
        placidus_distorted=chart.quality_flags.placidus_distorted,
        kp_on_equal_house=chart.quality_flags.kp_on_equal_house,
        is_retrospective=is_retrospective,
    )
