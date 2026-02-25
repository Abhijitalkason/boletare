"""
Jyotish AI — Test Ashtakavarga Computation

Validates BAV (Bhinnashtakavarga), SAV (Sarvashtakavarga), and
Trikona Shodhana reduction logic.
"""

from jyotish_ai.domain.types import Planet, Sign
from jyotish_ai.domain.models import AshtakavargaTable
from jyotish_ai.engine.ashtakavarga import compute_ashtakavarga


def test_compute_ashtakavarga_returns_valid_structure(sample_planets):
    """compute_ashtakavarga returns an AshtakavargaTable with all expected keys."""
    table = compute_ashtakavarga(sample_planets, ascendant_sign=Sign.ARIES)
    assert isinstance(table, AshtakavargaTable)
    # BAV should have 7 planet entries
    assert len(table.bav) == 7
    # Each BAV planet should have 12 sign entries
    for planet_name, sign_table in table.bav.items():
        assert len(sign_table) == 12, f"BAV for {planet_name} has {len(sign_table)} entries"
    # SAV should have 12 sign entries
    assert len(table.sav) == 12
    # Trikona reduced SAV should also have 12 sign entries
    assert len(table.sav_trikona_reduced) == 12


def test_bav_values_are_0_to_8(sample_planets):
    """Each BAV cell should be between 0 and 8 (8 contributors)."""
    table = compute_ashtakavarga(sample_planets, ascendant_sign=Sign.ARIES)
    for planet_name, sign_table in table.bav.items():
        for sign_name, points in sign_table.items():
            assert 0 <= points <= 8, (
                f"BAV[{planet_name}][{sign_name}] = {points}, expected 0-8"
            )


def test_sav_values_are_0_to_56(sample_planets):
    """SAV per sign is the sum of 7 BAV values, so it should be 0-56."""
    table = compute_ashtakavarga(sample_planets, ascendant_sign=Sign.ARIES)
    for sign_name, total in table.sav.items():
        assert 0 <= total <= 56, (
            f"SAV[{sign_name}] = {total}, expected 0-56"
        )


def test_trikona_shodhana_reduces_values(sample_planets):
    """Trikona-reduced SAV should be less than or equal to the original SAV for every sign."""
    table = compute_ashtakavarga(sample_planets, ascendant_sign=Sign.ARIES)
    for sign_name in table.sav:
        original = table.sav[sign_name]
        reduced = table.sav_trikona_reduced[sign_name]
        assert reduced <= original, (
            f"SAV_reduced[{sign_name}]={reduced} > SAV[{sign_name}]={original}"
        )
