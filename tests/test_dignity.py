"""
Jyotish AI — Test Dignity Scoring Engine

Validates that planetary dignities are classified correctly according
to classical Vedic rules: exaltation, debilitation, moolatrikona,
own sign, and friendship relationships.
"""

from jyotish_ai.domain.types import Planet, Sign, Dignity, ARCSEC_PER_SIGN, ARCSEC_PER_DEGREE
from jyotish_ai.engine.dignity import compute_dignity


def test_sun_in_aries_is_exalted():
    """Sun in Aries should be classified as EXALTED with score 1.0."""
    # Aries = sign 1, middle of the sign (15 degrees = 54000 arcsec)
    longitude = 54000  # 15 degrees Aries
    dignity, score = compute_dignity(Planet.SUN, longitude)
    assert dignity == Dignity.EXALTED
    assert score == 1.0


def test_sun_in_libra_is_debilitated():
    """Sun in Libra should be classified as DEBILITATED with score 0.0."""
    # Libra = sign 7, starts at 6 * 108000 = 648000
    longitude = 648000 + 54000  # 15 degrees Libra
    dignity, score = compute_dignity(Planet.SUN, longitude)
    assert dignity == Dignity.DEBILITATED
    assert score == 0.0


def test_mars_in_aries_0_to_12_is_moolatrikona():
    """Mars in Aries between 0 and 12 degrees should be MOOLATRIKONA with score 0.85."""
    # Aries starts at 0. Mars moolatrikona in Aries 0-12 degrees.
    # Test at 5 degrees = 5 * 3600 = 18000 arcsec
    longitude = 18000
    dignity, score = compute_dignity(Planet.MARS, longitude)
    assert dignity == Dignity.MOOLATRIKONA
    assert score == 0.85


def test_mars_in_scorpio_is_own():
    """Mars in Scorpio should be classified as OWN with score 0.75."""
    # Scorpio = sign 8, starts at 7 * 108000 = 756000
    # Mars moolatrikona is in Aries, not Scorpio, so own sign check applies
    longitude = 756000 + 54000  # 15 degrees Scorpio
    dignity, score = compute_dignity(Planet.MARS, longitude)
    assert dignity == Dignity.OWN
    assert score == 0.75


def test_saturn_in_leo_is_enemy():
    """Saturn in Leo should be ENEMY because Leo's lord is Sun, and Sun is Saturn's enemy."""
    # Leo = sign 5, starts at 4 * 108000 = 432000
    longitude = 432000 + 54000  # 15 degrees Leo
    dignity, score = compute_dignity(Planet.SATURN, longitude)
    assert dignity == Dignity.ENEMY
    assert score == 0.125
