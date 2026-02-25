"""
Jyotish AI -- Gate 1: Birth Chart Promise Analysis

Evaluates whether the natal (rasi) chart contains sufficient "promise"
for a given life event.  If the promise score falls below the threshold
(default 0.3), the prediction pipeline short-circuits and returns an
INSUFFICIENT confidence level -- no dasha or transit analysis is needed.

The promise score is a weighted combination of four sub-scores:

    1. House Lord Dignity   (weight 0.35)
       How well-placed is the lord of the event house?

    2. Occupant Analysis    (weight 0.15)
       Are natural benefics or malefics sitting in the event house?

    3. Navamsha Confirmation (weight 0.20)
       Does the D-9 chart support the event lord's strength?

    4. SAV Score            (weight 0.30)
       Sarva Ashtakavarga bindu count for the event sign.

All four sub-scores are normalised to [0.0, 1.0] before weighting.
"""

from __future__ import annotations

from jyotish_ai.domain.types import Planet, Sign, EventType, Dignity, DIGNITY_SCORE
from jyotish_ai.domain.models import (
    BirthChart,
    PlanetPosition,
    GateResult,
    AshtakavargaTable,
)
from jyotish_ai.domain.constants import (
    SIGN_LORD,
    EVENT_HOUSE_MAP,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    OWN_SIGNS,
    sign_to_house,
    house_to_sign,
    get_sign_from_arcsec,
)

# ── Sub-score weights ─────────────────────────────────────────────
_W_LORD_DIGNITY: float = 0.35
_W_OCCUPANT: float = 0.15
_W_NAVAMSHA: float = 0.20
_W_SAV: float = 0.30

# ── SAV normalisation bounds ──────────────────────────────────────
_SAV_MIN: int = 18
_SAV_MAX: int = 37

# ── Kendra and trikona house numbers (from lagna = house 1) ──────
_KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
_TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})
_KENDRA_TRIKONA_HOUSES: frozenset[int] = _KENDRA_HOUSES | _TRIKONA_HOUSES


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _find_planet(planets: list[PlanetPosition], target: Planet) -> PlanetPosition | None:
    """Return the PlanetPosition for *target* in *planets*, or None."""
    for pp in planets:
        if pp.planet == target:
            return pp
    return None


# ------------------------------------------------------------------
# Sub-score 1: House Lord Dignity
# ------------------------------------------------------------------

def _lord_dignity_score(
    chart: BirthChart,
    event_house: int,
) -> tuple[float, Sign, Planet]:
    """Return (dignity_score, event_sign, event_lord) for the event house.

    The dignity score comes directly from the event lord's
    ``PlanetPosition.dignity_score`` field (already 0.0-1.0).
    """
    event_sign: Sign = house_to_sign(event_house, chart.ascendant_sign)
    event_lord: Planet = SIGN_LORD[event_sign]

    lord_pos = _find_planet(chart.planets, event_lord)
    if lord_pos is None:
        # Should never happen for a valid chart; defensive fallback.
        return 0.0, event_sign, event_lord

    return lord_pos.dignity_score, event_sign, event_lord


# ------------------------------------------------------------------
# Sub-score 2: Occupant Analysis
# ------------------------------------------------------------------

def _occupant_score(
    chart: BirthChart,
    event_house: int,
) -> tuple[float, list[str], list[str]]:
    """Return (occupant_score, benefic_names, malefic_names).

    Each natural benefic in the event house adds +0.15.
    Each natural malefic in the event house subtracts 0.10.
    If the house is empty the score is 0.5 (neutral).
    The final value is clamped to [0.0, 1.0].
    """
    benefics_in_house: list[str] = []
    malefics_in_house: list[str] = []

    occupants = [pp for pp in chart.planets if pp.house == event_house]

    if not occupants:
        return 0.5, benefics_in_house, malefics_in_house

    score: float = 0.5  # start at neutral baseline
    for pp in occupants:
        if pp.planet in NATURAL_BENEFICS:
            score += 0.15
            benefics_in_house.append(pp.planet.value)
        if pp.planet in NATURAL_MALEFICS:
            score -= 0.10
            malefics_in_house.append(pp.planet.value)

    return _clamp(score), benefics_in_house, malefics_in_house


# ------------------------------------------------------------------
# Sub-score 3: Navamsha Confirmation
# ------------------------------------------------------------------

def _navamsha_score(
    chart: BirthChart,
    event_lord: Planet,
) -> float:
    """Check the event lord's placement in the navamsha (D-9) chart.

    Scoring:
        - Lord in own sign in navamsha           -> 1.0
        - Lord in kendra (1,4,7,10) or
          trikona (1,5,9) house in navamsha      -> 0.8
        - Otherwise                              -> 0.3
    """
    nav_pos = _find_planet(chart.navamsha_planets, event_lord)
    if nav_pos is None:
        return 0.3

    # Check own sign first (higher score takes priority).
    own_signs = OWN_SIGNS.get(event_lord, [])
    if nav_pos.sign in own_signs:
        return 1.0

    # Check kendra / trikona placement.
    if nav_pos.house in _KENDRA_TRIKONA_HOUSES:
        return 0.8

    return 0.3


# ------------------------------------------------------------------
# Sub-score 4: SAV (Sarva Ashtakavarga) Score
# ------------------------------------------------------------------

def _sav_score(
    chart: BirthChart,
    event_sign: Sign,
) -> tuple[float, int]:
    """Return (normalised_sav, raw_sav) for the event sign.

    Normalisation: ``(raw - 18) / (37 - 18)`` clamped to [0.0, 1.0].
    A raw SAV >= 28 is considered favourable in classical texts.
    """
    sav_key: str = event_sign.name  # e.g. "ARIES"
    raw: int = chart.ashtakavarga.sav.get(sav_key, _SAV_MIN)
    normalised: float = _clamp((raw - _SAV_MIN) / (_SAV_MAX - _SAV_MIN))
    return normalised, raw


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def evaluate_promise(
    chart: BirthChart,
    event_type: EventType,
    promise_threshold: float = 0.3,
) -> GateResult:
    """Gate 1: Evaluate birth chart promise for an event type.

    Args:
        chart: Complete birth chart produced by Layer 1.
        event_type: The life event being predicted (e.g. MARRIAGE).
        promise_threshold: Minimum composite score for the gate to
            pass.  Defaults to 0.3.

    Returns:
        A ``GateResult`` containing the normalised score (0.0-1.0),
        a boolean sufficiency flag, and a ``details`` dict with every
        sub-score and the planets/signs involved.
    """
    # ── Resolve event house and lord ──────────────────────────────
    event_house: int = EVENT_HOUSE_MAP[event_type]

    lord_dignity, event_sign, event_lord = _lord_dignity_score(
        chart, event_house,
    )

    # ── Compute each sub-score ────────────────────────────────────
    occupant, benefics_in_house, malefics_in_house = _occupant_score(
        chart, event_house,
    )

    navamsha = _navamsha_score(chart, event_lord)

    sav_normalized, sav_value = _sav_score(chart, event_sign)

    # ── Weighted composite ────────────────────────────────────────
    score: float = (
        _W_LORD_DIGNITY * lord_dignity
        + _W_OCCUPANT * occupant
        + _W_NAVAMSHA * navamsha
        + _W_SAV * sav_normalized
    )
    score = _clamp(score)

    # ── Assemble result ───────────────────────────────────────────
    details: dict = {
        "event_house": event_house,
        "event_sign": event_sign.name,
        "event_lord": event_lord.value,
        "lord_dignity": lord_dignity,
        "occupant_score": occupant,
        "navamsha_score": navamsha,
        "sav_raw": sav_value,
        "sav_normalized": sav_normalized,
        "benefics_in_house": benefics_in_house,
        "malefics_in_house": malefics_in_house,
    }

    return GateResult(
        gate_name="gate1_promise",
        score=score,
        is_sufficient=score >= promise_threshold,
        details=details,
    )
