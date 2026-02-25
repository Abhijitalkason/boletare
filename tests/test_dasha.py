"""
Jyotish AI — Test Vimshottari Dasha Engine

Validates dasha tree computation, period durations, active period lookup,
and sub-period counts.
"""

from datetime import date

from jyotish_ai.domain.types import Planet, DashaLevel, ARCSEC_PER_NAKSHATRA
from jyotish_ai.engine.dasha import compute_dasha_tree, find_active_periods


def test_compute_dasha_tree_returns_9_mahadashas():
    """The Vimshottari system always produces exactly 9 mahadashas."""
    # Moon at 0 arcsec (start of Ashwini nakshatra, lord = Ketu)
    tree = compute_dasha_tree(moon_arcsec=0, birth_date=date(1990, 1, 15))
    assert len(tree) == 9
    # All should be mahadashas
    for md in tree:
        assert md.level == DashaLevel.MAHADASHA


def test_first_dasha_has_reduced_duration():
    """The first mahadasha should have its duration reduced by the elapsed fraction."""
    # Moon at midpoint of Ashwini (24000 arcsec = 50% through nakshatra)
    # Ashwini lord = Ketu (7 years total). Elapsed fraction = 0.5, remaining = 0.5
    tree = compute_dasha_tree(moon_arcsec=24000, birth_date=date(1990, 1, 15))
    first_md = tree[0]
    assert first_md.planet == Planet.KETU
    # Full Ketu dasha = 7 years = 7 * 365.25 = 2556.75 days
    # Remaining should be approximately half
    expected_days = 7 * 365.25 * 0.5
    assert abs(first_md.duration_days - expected_days) < 1.0


def test_total_dasha_duration_approx_120_years():
    """Total duration of all 9 mahadashas should approximate 120 years."""
    # Moon at start of nakshatra (0 elapsed) -> full 120 years
    tree = compute_dasha_tree(moon_arcsec=0, birth_date=date(1990, 1, 15))
    total_days = sum(md.duration_days for md in tree)
    expected_days = 120 * 365.25  # 43830
    assert abs(total_days - expected_days) < 10.0, (
        f"Total days {total_days} differs from expected {expected_days} by more than 10 days"
    )


def test_find_active_periods_returns_correct_mahadasha():
    """find_active_periods returns the correct MD and AD for a given date."""
    tree = compute_dasha_tree(moon_arcsec=0, birth_date=date(1990, 1, 15))
    # Query during the first mahadasha
    query = date(1992, 6, 15)
    md, ad = find_active_periods(tree, query)
    assert md is not None
    assert md.start_date <= query <= md.end_date
    # Check that the mahadasha planet matches the expected first dasha lord
    assert md.planet == tree[0].planet
    # Antardasha should also be found
    assert ad is not None
    assert ad.start_date <= query <= ad.end_date


def test_sub_periods_count_is_9_per_mahadasha():
    """Each mahadasha should contain exactly 9 antardasha sub-periods."""
    tree = compute_dasha_tree(moon_arcsec=0, birth_date=date(1990, 1, 15))
    for md in tree:
        assert len(md.sub_periods) == 9, (
            f"MD {md.planet.value} has {len(md.sub_periods)} sub-periods, expected 9"
        )
        for ad in md.sub_periods:
            assert ad.level == DashaLevel.ANTARDASHA
