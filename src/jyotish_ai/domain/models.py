"""
Jyotish AI — Domain Models (Pydantic v2)

Pure domain objects for the Jyotish AI engine.  No database or I/O
concerns — these are the data structures that flow between layers.

Layer 1 (Compute) produces a BirthChart.
Layer 2 (Predict) produces a PredictionResult.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from jyotish_ai.domain.types import (
    Planet,
    Sign,
    EventType,
    ConfidenceLevel,
    BirthTimeTier,
    LagnaMode,
    DashaLevel,
    Dignity,
    ArcSeconds,
)


# ──────────────────────────────────────────────────────────────────────
# 1. PlanetPosition — A planet's computed position
# ──────────────────────────────────────────────────────────────────────
class PlanetPosition(BaseModel):
    """A single planet's sidereal position and dignity.

    All positional math is carried out in integer arc-seconds to avoid
    floating-point boundary errors.  Display-friendly degree values are
    derived and stored alongside the canonical arc-second value.
    """

    planet: Planet
    longitude_arcsec: int = Field(
        ge=0,
        lt=1_296_000,
        description="Absolute sidereal longitude in arc-seconds (0 to 1 295 999).",
    )
    sign: Sign = Field(
        description="Zodiac sign derived from longitude_arcsec // 108 000 + 1.",
    )
    sign_degrees: float = Field(
        description="Degrees within the sign, for display (0.0 – 30.0).",
    )
    nakshatra: str = Field(
        description="Nakshatra name (e.g. 'Ashwini', 'Bharani', …).",
    )
    nakshatra_pada: int = Field(
        ge=1,
        le=4,
        description="Nakshatra pada (quarter), 1-4.",
    )
    house: int = Field(
        ge=1,
        le=12,
        description="House number (1-12), assigned after house computation.",
    )
    dignity: Dignity
    dignity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Numeric dignity score (0.0 = debilitated, 1.0 = exalted).",
    )
    is_retrograde: bool = False


# ──────────────────────────────────────────────────────────────────────
# 2. HouseCusp — A house cusp position
# ──────────────────────────────────────────────────────────────────────
class HouseCusp(BaseModel):
    """One of the twelve house cusps."""

    house_number: int = Field(ge=1, le=12, description="House number (1-12).")
    cusp_arcsec: int = Field(
        ge=0,
        lt=1_296_000,
        description="Cusp longitude in arc-seconds.",
    )
    sign: Sign
    sign_degrees: float = Field(
        description="Degrees of the cusp within the sign (0.0 – 30.0).",
    )
    span_degrees: float = Field(
        description="Angular span of this house in degrees.",
    )


# ──────────────────────────────────────────────────────────────────────
# 3. DashaPeriod — A single dasha period (recursive)
# ──────────────────────────────────────────────────────────────────────
class DashaPeriod(BaseModel):
    """A single Vimshottari dasha period.

    Recursive: a Mahadasha contains Antardashas in ``sub_periods``,
    and each Antardasha can contain Pratyantardashas.
    """

    level: DashaLevel
    planet: Planet
    start_date: date
    end_date: date
    duration_days: float = Field(
        description="Duration in days (fractional for sub-periods).",
    )
    sub_periods: list[DashaPeriod] = Field(
        default_factory=list,
        description="Nested sub-periods (AD within MD, PAD within AD).",
    )


# ──────────────────────────────────────────────────────────────────────
# 4. BoundaryFlags — Results of dual-ephemeris boundary detection
# ──────────────────────────────────────────────────────────────────────
class BoundaryFlags(BaseModel):
    """Flags raised when birth-time uncertainty places key points near
    sign, nakshatra, or dasha boundaries.

    These drive the dual-tree / Chandra-lagna failover logic.
    """

    lagna_ambiguous: bool = False
    moon_nakshatra_boundary: bool = False
    moon_sign_boundary: bool = False
    dasha_boundary_sensitive: bool = False


# ──────────────────────────────────────────────────────────────────────
# 5. QualityFlags — Every prediction carries these
# ──────────────────────────────────────────────────────────────────────
class QualityFlags(BaseModel):
    """Metadata flags that travel with every prediction so downstream
    consumers (UI, narrator, audit) know how much to trust the result.
    """

    birth_time_tier: BirthTimeTier
    lagna_mode: LagnaMode = LagnaMode.STANDARD
    dasha_boundary_sensitive: bool = False
    dasha_ambiguous: bool = False
    placidus_distorted: bool = False
    kp_on_equal_house: bool = False
    is_retrospective: bool = False


# ──────────────────────────────────────────────────────────────────────
# 6. AshtakavargaTable — BAV + SAV scores
# ──────────────────────────────────────────────────────────────────────
class AshtakavargaTable(BaseModel):
    """Ashtakavarga bindus — both individual (BAV) and aggregate (SAV).

    Keys are canonical string names so the table serialises to clean
    JSON.  Planet names match ``Planet.value``; sign names match
    ``Sign.name``.
    """

    bav: dict[str, dict[str, int]] = Field(
        description=(
            "Bhinna Ashtakavarga: planet_name -> sign_name -> points (0-8)."
        ),
    )
    sav: dict[str, int] = Field(
        description="Sarva Ashtakavarga: sign_name -> total points (0-56).",
    )
    sav_trikona_reduced: dict[str, int] = Field(
        description="SAV after Trikona Shodhana reduction.",
    )


# ──────────────────────────────────────────────────────────────────────
# 7. BirthChart — Complete computed birth chart (Layer 1 output)
# ──────────────────────────────────────────────────────────────────────
class BirthChart(BaseModel):
    """The complete, immutable birth chart produced by Layer 1 (Compute).

    Contains every datum the prediction engine needs: planetary
    positions (rasi and navamsha), houses, dashas, ashtakavarga,
    and all quality/boundary metadata.
    """

    ascendant_sign: Sign
    ascendant_arcsec: int = Field(
        ge=0,
        lt=1_296_000,
        description="Ascendant longitude in arc-seconds.",
    )
    lagna_mode: LagnaMode
    planets: list[PlanetPosition]
    houses: list[HouseCusp]
    dasha_tree: list[DashaPeriod]
    dasha_tree_alt: Optional[list[DashaPeriod]] = Field(
        default=None,
        description="Second dasha tree when boundary-sensitive.",
    )
    ashtakavarga: AshtakavargaTable
    navamsha_planets: list[PlanetPosition]
    boundary_flags: BoundaryFlags
    quality_flags: QualityFlags
    computed_at: datetime


# ──────────────────────────────────────────────────────────────────────
# 8. GateResult — Output of a single gate evaluation
# ──────────────────────────────────────────────────────────────────────
class GateResult(BaseModel):
    """Result from one of the three prediction gates.

    Each gate produces a 0-1 score and a boolean sufficiency flag.
    ``details`` carries gate-specific sub-scores and human-readable
    explanations used by the narrator.
    """

    gate_name: str
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Gate score normalised to 0.0 – 1.0.",
    )
    is_sufficient: bool = Field(
        description="Whether this gate alone passes its threshold.",
    )
    details: dict = Field(
        default_factory=dict,
        description="Gate-specific sub-scores and explanations.",
    )


# ──────────────────────────────────────────────────────────────────────
# 9. TransitWindow — A month in the transit scan
# ──────────────────────────────────────────────────────────────────────
class TransitWindow(BaseModel):
    """A single calendar month evaluated during the transit scan (Gate 3).

    Captures Jupiter and Saturn positions plus the double-transit
    activation flag and BAV transit score.
    """

    month: str = Field(
        pattern=r"^\d{4}-\d{2}$",
        description="Calendar month in YYYY-MM format.",
    )
    jupiter_sign: str
    saturn_sign: str
    jupiter_house: int = Field(ge=1, le=12)
    saturn_house: int = Field(ge=1, le=12)
    jupiter_in_favorable: bool
    saturn_in_favorable: bool
    double_transit_active: bool
    transit_bav_score: float


# ──────────────────────────────────────────────────────────────────────
# 10. PredictionResult — Complete prediction output (Layer 2 output)
# ──────────────────────────────────────────────────────────────────────
class PredictionResult(BaseModel):
    """The full prediction produced by Layer 2 (Predict).

    Aggregates the three gate results, convergence scoring, timeline,
    narrative text, and all quality metadata needed for display and
    audit.
    """

    user_id: int
    event_type: EventType
    query_date: date
    gate1: GateResult
    gate2: GateResult
    gate3: GateResult
    convergence_score: float = Field(
        description="Weighted sum of gate scores driving confidence level.",
    )
    confidence_level: ConfidenceLevel
    quality_flags: QualityFlags
    timeline: list[TransitWindow]
    peak_month: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}$",
        description="YYYY-MM of the highest-scoring transit month.",
    )
    feature_vector: list[float] = Field(
        default_factory=list,
        description="Numeric feature vector for ML calibration layer.",
    )
    narration_text: Optional[str] = Field(
        default=None,
        description="Human-readable narrative generated by the narrator.",
    )
    is_retrospective: bool = False
    created_at: datetime


# ──────────────────────────────────────────────────────────────────────
# 11. YogaResult — A classical yoga detected in the birth chart
# ──────────────────────────────────────────────────────────────────────
class YogaResult(BaseModel):
    """A yoga (planetary combination) detected in the birth chart."""

    name: str = Field(description="Display name, e.g. 'Gajakesari Yoga'.")
    yoga_type: str = Field(
        description="Category: 'mahapurusha', 'raj', 'dhana', 'conjunction', 'viparita'.",
    )
    is_present: bool
    strength: float = Field(
        ge=0.0, le=1.0,
        description="0 = barely formed, 1 = textbook perfect.",
    )
    involved_planets: list[str] = Field(
        description="Planet names involved, e.g. ['Jupiter', 'Moon'].",
    )
    description: str = Field(description="One-line classical interpretation.")


# ──────────────────────────────────────────────────────────────────────
# 12. DoshaResult — A dosha (affliction) detected in the birth chart
# ──────────────────────────────────────────────────────────────────────
class DoshaResult(BaseModel):
    """A dosha (affliction) detected in the birth chart."""

    name: str = Field(description="Display name, e.g. 'Mangal Dosha'.")
    is_present: bool
    severity: str = Field(
        default="none",
        description="'none', 'mild', 'moderate', or 'severe'.",
    )
    involved_planets: list[str]
    affected_houses: list[int]
    description: str
    cancellation_factors: list[str] = Field(default_factory=list)
