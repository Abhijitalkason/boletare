"""
Jyotish AI — Test Quality Flag Computation

Validates that quality flags are correctly assembled from birth chart metadata
and prediction context.
"""

from datetime import date, datetime

from jyotish_ai.domain.types import (
    Planet, Sign, BirthTimeTier, LagnaMode, DashaLevel, Dignity,
    ARCSEC_PER_SIGN,
)
from jyotish_ai.domain.models import (
    PlanetPosition, HouseCusp, DashaPeriod, BoundaryFlags, QualityFlags,
    AshtakavargaTable, BirthChart,
)
from jyotish_ai.prediction.quality_flags import compute_quality_flags


def test_standard_flags_from_chart(sample_chart):
    """Quality flags should reflect the chart's birth_time_tier, lagna_mode, and boundary flags."""
    flags = compute_quality_flags(sample_chart)
    assert flags.birth_time_tier == BirthTimeTier.TIER_2
    assert flags.lagna_mode == LagnaMode.STANDARD
    assert flags.dasha_boundary_sensitive is False
    assert flags.dasha_ambiguous is False
    assert flags.is_retrospective is False


def test_retrospective_flag(sample_chart):
    """Setting is_retrospective=True should be reflected in the quality flags."""
    flags = compute_quality_flags(sample_chart, is_retrospective=True)
    assert flags.is_retrospective is True


def test_dasha_ambiguous_when_alt_tree_present(sample_chart):
    """When dasha_tree_alt is not None, the dasha_ambiguous flag should be True."""
    # Create a chart with an alternate dasha tree
    alt_tree = [DashaPeriod(
        level=DashaLevel.MAHADASHA,
        planet=Planet.SUN,
        start_date=date(1988, 1, 1),
        end_date=date(1994, 1, 1),
        duration_days=2191.5,
    )]
    chart_with_alt = sample_chart.model_copy(update={"dasha_tree_alt": alt_tree})
    flags = compute_quality_flags(chart_with_alt)
    assert flags.dasha_ambiguous is True
