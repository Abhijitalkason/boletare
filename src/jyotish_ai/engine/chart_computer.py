"""
Jyotish AI — Layer 1 Orchestrator: Chart Computer

THE central orchestrator for the entire compute layer.  Every birth chart
computation flows through the single public function ``compute_birth_chart()``,
which wires together all Layer 1 modules in the correct order:

    ephemeris  ->  boundary  ->  houses  ->  dignity  ->  dasha
                                                      ->  ashtakavarga
                                                      ->  navamsha

Responsibilities
----------------
1. Convert user-supplied birth date/time/place into a Julian Day.
2. Run dual-ephemeris boundary detection to identify ambiguous positions.
3. Compute all 9 Vedic planet longitudes (sidereal, integer arc-seconds).
4. Compute house cusps (Placidus with distortion detection).
5. Apply KP-specific fallback: if Placidus is distorted AND ayanamsha is
   "kp", switch to Equal House system.
6. Apply Chandra Lagna failover when the ascendant sign is ambiguous
   (Tier 3 birth times with lagna on a sign boundary).
7. Assign planets to houses, compute dignities, build PlanetPosition objects.
8. Compute Vimshottari Dasha tree (with an alternate tree when the Moon is
   on a Nakshatra boundary).
9. Compute Ashtakavarga (BAV + SAV + Trikona Shodhana).
10. Compute Navamsha (D-9) divisional chart.
11. Assemble and return the immutable ``BirthChart`` object.

Design invariants
-----------------
* All positional values are integer arc-seconds — no floats in positional math.
* ``compute_birth_chart`` is the ONLY entry point for chart computation.
* Every downstream consumer (prediction engine, narrator, API) receives the
  same ``BirthChart`` object with identical quality metadata.
* The function is pure-functional: no side effects, no database I/O.
"""

from __future__ import annotations

from datetime import date, time, datetime
from typing import Optional

from jyotish_ai.domain.types import (
    Planet,
    Sign,
    BirthTimeTier,
    LagnaMode,
    Dignity,
    ArcSeconds,
    ARCSEC_PER_SIGN,
    ARCSEC_FULL_CIRCLE,
    TIER_UNCERTAINTY_MINUTES,
)
from jyotish_ai.domain.models import (
    BirthChart,
    PlanetPosition,
    HouseCusp,
    DashaPeriod,
    BoundaryFlags,
    QualityFlags,
    AshtakavargaTable,
)
from jyotish_ai.domain.constants import (
    SIGN_LORD,
    get_sign_from_arcsec,
    get_nakshatra_name,
    get_pada,
)
from jyotish_ai.engine.ephemeris import (
    date_to_jd,
    get_all_planet_longitudes,
    arcsec_to_sign,
    arcsec_to_deg,
    arcsec_in_sign,
)
from jyotish_ai.engine.houses import (
    compute_houses,
    compute_equal_houses_from_asc,
    assign_planet_to_house,
)
from jyotish_ai.engine.boundary import check_boundaries
from jyotish_ai.engine.dasha import compute_dasha_tree
from jyotish_ai.engine.ashtakavarga import compute_ashtakavarga
from jyotish_ai.engine.navamsha import compute_navamsha
from jyotish_ai.engine.dignity import compute_dignity

# Arc-seconds per Nakshatra (13 deg 20 min = 48,000 arcsec).
# Used for the alternate Dasha tree offset.
_ARCSEC_PER_NAKSHATRA: int = 48_000


# ======================================================================
# Public API — the single entry point for Layer 1
# ======================================================================

def compute_birth_chart(
    birth_date: date,
    birth_time: Optional[time] = None,
    latitude: float = 28.6,       # Delhi default
    longitude: float = 77.2,
    tz_offset: float = 5.5,       # IST
    birth_time_tier: BirthTimeTier = BirthTimeTier.TIER_2,
    ayanamsha: str = "lahiri",
) -> BirthChart:
    """Compute the complete birth chart — Layer 1 orchestrator.

    This function is the sole entry point for producing a ``BirthChart``.
    It coordinates every Layer 1 sub-module in the precise sequence required
    by the architecture, applying failover logic (Chandra Lagna, Equal Houses)
    and dual-tree Dasha computation when boundary ambiguity is detected.

    Args:
        birth_date:
            Date of birth.
        birth_time:
            Time of birth.  If ``None``, defaults to approximate sunrise
            (06:00 local time) — suitable for rough estimates.
        latitude:
            Birth latitude in decimal degrees (positive = North).
            Defaults to Delhi (28.6 N).
        longitude:
            Birth longitude in decimal degrees (positive = East).
            Defaults to Delhi (77.2 E).
        tz_offset:
            Timezone offset from UTC in hours.  IST = +5.5 (default).
        birth_time_tier:
            Confidence level of the birth time.

            * ``TIER_1`` — hospital certificate, +/- 2 min
            * ``TIER_2`` — family memory, +/- 15 min (default)
            * ``TIER_3`` — rough estimate, +/- 30 min
        ayanamsha:
            Sidereal ayanamsha method: ``"lahiri"`` (default) or ``"kp"``
            (Krishnamurti Paddhati).

    Returns:
        A fully populated ``BirthChart`` containing planet positions (rasi
        and navamsha), house cusps, Vimshottari Dasha tree(s), Ashtakavarga
        tables, and all quality/boundary metadata.

    Steps executed (in order):
        1.  Convert birth date/time to Julian Day.
        2.  Run dual-ephemeris boundary detection.
        3.  Compute all 9 planet longitudes.
        4.  Compute house cusps (Placidus + distortion detection).
        5.  If Placidus distorted AND ayanamsha == "kp" -> use Equal Houses.
        6.  If lagna_ambiguous (boundary flags) -> switch to Chandra Lagna.
        7.  Assign planets to houses.
        8.  Compute planetary dignities.
        9.  Build PlanetPosition objects.
        10. Compute Vimshottari Dasha tree (+ alternate if boundary sensitive).
        11. Compute Ashtakavarga (BAV + SAV + Trikona Shodhana).
        12. Compute Navamsha (D-9).
        13. Assemble QualityFlags.
        14. Return BirthChart.
    """

    # ──────────────────────────────────────────────────────────────
    # Step 1: Convert birth date/time to Julian Day
    # ──────────────────────────────────────────────────────────────
    jd: float = date_to_jd(birth_date, birth_time, tz_offset)

    # ──────────────────────────────────────────────────────────────
    # Step 2: Dual-ephemeris boundary detection
    #   Flags raised here drive Chandra Lagna failover and dual
    #   Dasha tree logic further down.
    # ──────────────────────────────────────────────────────────────
    boundary_flags: BoundaryFlags = check_boundaries(
        birth_jd=jd,
        birth_time_tier=birth_time_tier,
        ayanamsha=ayanamsha,
        latitude=latitude,
        longitude=longitude,
    )

    # ──────────────────────────────────────────────────────────────
    # Step 3: Compute all 9 planet longitudes (sidereal, arc-seconds)
    #   Returns {Planet: (arcsec, is_retrograde)} for all 9 grahas.
    # ──────────────────────────────────────────────────────────────
    planet_longitudes: dict[Planet, tuple[ArcSeconds, bool]] = (
        get_all_planet_longitudes(jd, ayanamsha)
    )

    # ──────────────────────────────────────────────────────────────
    # Step 4: Compute house cusps (Placidus + distortion detection)
    #   compute_houses returns (list[HouseCusp], ascendant_arcsec, placidus_distorted)
    # ──────────────────────────────────────────────────────────────
    houses: list[HouseCusp]
    ascendant_arcsec: int
    placidus_distorted: bool
    houses, ascendant_arcsec, placidus_distorted = compute_houses(
        jd, latitude, longitude, ayanamsha
    )

    # ──────────────────────────────────────────────────────────────
    # Step 5: KP Equal House fallback
    #   When using KP ayanamsha and Placidus produces distorted
    #   houses (any span > 40 deg or < 20 deg), fall back to
    #   Equal House system.  This ensures KP sub-lord assignments
    #   remain meaningful.
    # ──────────────────────────────────────────────────────────────
    kp_on_equal_house: bool = False
    if placidus_distorted and ayanamsha == "kp":
        houses = compute_equal_houses_from_asc(ascendant_arcsec)
        kp_on_equal_house = True

    # ──────────────────────────────────────────────────────────────
    # Step 6: Chandra Lagna failover
    #   When the ascendant sign is ambiguous (boundary detection
    #   found that the lagna sign changes within the uncertainty
    #   window), we cannot trust the rising sign.  Switch to
    #   Chandra Lagna mode: use the Moon's sign as the effective
    #   ascendant, and recompute houses using Equal Houses from
    #   the Moon's position.
    # ──────────────────────────────────────────────────────────────
    lagna_mode: LagnaMode = LagnaMode.STANDARD

    if boundary_flags.lagna_ambiguous:
        lagna_mode = LagnaMode.CHANDRA

        # Retrieve Moon's longitude from the computed positions
        moon_arcsec_raw, _ = planet_longitudes[Planet.MOON]
        moon_sign: Sign = arcsec_to_sign(moon_arcsec_raw)

        # Moon's position becomes the effective ascendant
        ascendant_arcsec = int(moon_arcsec_raw)

        # Recompute houses as Equal Houses from the Moon's position
        houses = compute_equal_houses_from_asc(ascendant_arcsec)

    # Derive the ascendant sign from the (possibly updated) ascendant
    ascendant_sign: Sign = arcsec_to_sign(ascendant_arcsec)

    # ──────────────────────────────────────────────────────────────
    # Steps 7-9: Build PlanetPosition objects
    #   For each planet: assign house, compute dignity, build the
    #   full PlanetPosition with all derived fields.
    # ──────────────────────────────────────────────────────────────
    planets: list[PlanetPosition] = _build_planet_positions(
        planet_longitudes=planet_longitudes,
        houses=houses,
    )

    # ──────────────────────────────────────────────────────────────
    # Step 10: Vimshottari Dasha tree
    #   Always compute from Moon's actual arc-second position.
    #   When the Moon is on a Nakshatra boundary (dasha_boundary_sensitive),
    #   also compute an alternate tree with Moon shifted one
    #   Nakshatra forward (48,000 arcsec) to capture both possible
    #   Dasha sequences.
    # ──────────────────────────────────────────────────────────────
    moon_arcsec: int = int(planet_longitudes[Planet.MOON][0])

    dasha_tree: list[DashaPeriod] = compute_dasha_tree(
        moon_arcsec=moon_arcsec,
        birth_date=birth_date,
    )

    dasha_tree_alt: Optional[list[DashaPeriod]] = None
    if boundary_flags.dasha_boundary_sensitive:
        # Shift Moon forward by one Nakshatra (48,000 arcsec) to compute
        # the alternate Dasha sequence on the other side of the boundary
        alt_moon_arcsec = (moon_arcsec + _ARCSEC_PER_NAKSHATRA) % ARCSEC_FULL_CIRCLE
        dasha_tree_alt = compute_dasha_tree(
            moon_arcsec=alt_moon_arcsec,
            birth_date=birth_date,
        )

    # ──────────────────────────────────────────────────────────────
    # Step 11: Ashtakavarga (BAV + SAV + Trikona Shodhana)
    #   Uses the rasi planet positions and the effective ascendant sign.
    # ──────────────────────────────────────────────────────────────
    ashtakavarga: AshtakavargaTable = compute_ashtakavarga(
        planets=planets,
        ascendant_sign=ascendant_sign,
    )

    # ──────────────────────────────────────────────────────────────
    # Step 12: Navamsha (D-9) divisional chart
    #   Computes navamsha sign and synthetic longitude for each planet.
    # ──────────────────────────────────────────────────────────────
    navamsha_planets: list[PlanetPosition] = compute_navamsha(planets)

    # ──────────────────────────────────────────────────────────────
    # Step 13: Assemble QualityFlags
    #   These metadata flags travel with every prediction so that
    #   downstream consumers (UI, narrator, audit) know how much
    #   to trust the result.
    # ──────────────────────────────────────────────────────────────
    quality_flags: QualityFlags = QualityFlags(
        birth_time_tier=birth_time_tier,
        lagna_mode=lagna_mode,
        dasha_boundary_sensitive=boundary_flags.dasha_boundary_sensitive,
        dasha_ambiguous=(
            boundary_flags.dasha_boundary_sensitive
            and boundary_flags.moon_sign_boundary
        ),
        placidus_distorted=placidus_distorted,
        kp_on_equal_house=kp_on_equal_house,
        is_retrospective=False,
    )

    # ──────────────────────────────────────────────────────────────
    # Step 14: Assemble and return the immutable BirthChart
    # ──────────────────────────────────────────────────────────────
    return BirthChart(
        ascendant_sign=ascendant_sign,
        ascendant_arcsec=ascendant_arcsec,
        lagna_mode=lagna_mode,
        planets=planets,
        houses=houses,
        dasha_tree=dasha_tree,
        dasha_tree_alt=dasha_tree_alt,
        ashtakavarga=ashtakavarga,
        navamsha_planets=navamsha_planets,
        boundary_flags=boundary_flags,
        quality_flags=quality_flags,
        computed_at=datetime.utcnow(),
    )


# ======================================================================
# Internal helpers
# ======================================================================

def _build_planet_positions(
    planet_longitudes: dict[Planet, tuple[ArcSeconds, bool]],
    houses: list[HouseCusp],
) -> list[PlanetPosition]:
    """Build the list of PlanetPosition objects from raw ephemeris data.

    For each of the 9 Vedic planets, this function:
    1. Extracts the arc-second longitude and retrograde flag from the
       ephemeris output.
    2. Derives the zodiac sign, degree within sign, nakshatra, and pada.
    3. Assigns the planet to a house using the computed house cusps.
    4. Computes the classical dignity and numeric score.
    5. Assembles the full ``PlanetPosition`` model.

    The resulting list is ordered by the ``Planet`` enum iteration order
    (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).

    Args:
        planet_longitudes:
            Output of ``get_all_planet_longitudes()``: a mapping of
            Planet to (longitude_arcsec, is_retrograde).
        houses:
            List of 12 ``HouseCusp`` objects for house assignment.

    Returns:
        List of 9 ``PlanetPosition`` objects, one per Vedic planet.
    """
    positions: list[PlanetPosition] = []

    for planet in Planet:
        arcsec, is_retro = planet_longitudes[planet]
        arcsec_int: int = int(arcsec)

        # Zodiac sign (1-12)
        sign: Sign = arcsec_to_sign(arcsec_int)

        # Degrees within the sign (0.0 to ~30.0) for display
        sign_deg: float = arcsec_in_sign(arcsec_int) / 3600.0

        # Nakshatra name and pada (quarter, 1-4)
        nak_name: str = get_nakshatra_name(arcsec_int)
        pada: int = get_pada(arcsec_int)

        # House assignment (1-12) using house cusp boundaries
        house: int = assign_planet_to_house(arcsec_int, houses)

        # Classical dignity and numeric score (0.0 to 1.0)
        dignity_enum: Dignity
        dignity_score: float
        dignity_enum, dignity_score = compute_dignity(planet, arcsec_int)

        positions.append(PlanetPosition(
            planet=planet,
            longitude_arcsec=arcsec_int,
            sign=sign,
            sign_degrees=round(sign_deg, 4),
            nakshatra=nak_name,
            nakshatra_pada=pada,
            house=house,
            dignity=dignity_enum,
            dignity_score=dignity_score,
            is_retrograde=is_retro,
        ))

    return positions
