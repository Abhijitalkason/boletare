"""
Jyotish AI — Core Domain Types

ArcSeconds is THE fundamental type. Every positional value in the system
flows through integer arc-seconds to eliminate floating-point boundary errors.

1 degree = 3,600 arc-seconds
1 sign (30°) = 108,000 arc-seconds
1 nakshatra (13°20') = 48,000 arc-seconds
Full zodiac (360°) = 1,296,000 arc-seconds
"""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import NewType

# ──────────────────────────────────────────────────────────────────
# THE fundamental type — all positional math uses this
# ──────────────────────────────────────────────────────────────────
ArcSeconds = NewType("ArcSeconds", int)

# Conversion constants
ARCSEC_PER_DEGREE: int = 3_600
ARCSEC_PER_SIGN: int = 108_000       # 30 * 3600
ARCSEC_PER_NAKSHATRA: int = 48_000   # 13.3333... * 3600
ARCSEC_PER_PADA: int = 12_000        # 3.3333... * 3600  (nakshatra / 4)
ARCSEC_FULL_CIRCLE: int = 1_296_000  # 360 * 3600


# ──────────────────────────────────────────────────────────────────
# Planets — 9 Vedic Grahas
# ──────────────────────────────────────────────────────────────────
class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"


# ──────────────────────────────────────────────────────────────────
# Zodiac Signs — 1-indexed IntEnum for arithmetic
# ──────────────────────────────────────────────────────────────────
class Sign(IntEnum):
    ARIES = 1
    TAURUS = 2
    GEMINI = 3
    CANCER = 4
    LEO = 5
    VIRGO = 6
    LIBRA = 7
    SCORPIO = 8
    SAGITTARIUS = 9
    CAPRICORN = 10
    AQUARIUS = 11
    PISCES = 12


# ──────────────────────────────────────────────────────────────────
# Event Types — life events the engine can predict
# ──────────────────────────────────────────────────────────────────
class EventType(str, Enum):
    MARRIAGE = "marriage"
    CAREER = "career"
    CHILD = "child"
    PROPERTY = "property"
    HEALTH = "health"


# ──────────────────────────────────────────────────────────────────
# Confidence Levels — prediction confidence classification
# ──────────────────────────────────────────────────────────────────
class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"           # convergence >= 2.5
    MEDIUM = "MEDIUM"       # convergence >= 1.5
    LOW = "LOW"             # convergence >= 0.5
    NEGATIVE = "NEGATIVE"   # convergence < 0.5
    INSUFFICIENT = "INSUFFICIENT"  # Gate 1 below promise threshold


# ──────────────────────────────────────────────────────────────────
# Birth Time Confidence Tiers
# ──────────────────────────────────────────────────────────────────
class BirthTimeTier(IntEnum):
    """Birth time confidence.

    Tier 1: Hospital certificate (±2 min)  — ~20% of users
    Tier 2: Family memory (±15 min)        — ~50% of users
    Tier 3: Rough estimate (±30 min)       — ~30% of users
    """
    TIER_1 = 1  # ±2 min
    TIER_2 = 2  # ±15 min
    TIER_3 = 3  # ±30 min


# Uncertainty in minutes for each tier
TIER_UNCERTAINTY_MINUTES: dict[BirthTimeTier, float] = {
    BirthTimeTier.TIER_1: 2.0,
    BirthTimeTier.TIER_2: 15.0,
    BirthTimeTier.TIER_3: 30.0,
}


# ──────────────────────────────────────────────────────────────────
# Lagna Mode — standard vs Chandra Lagna failover
# ──────────────────────────────────────────────────────────────────
class LagnaMode(str, Enum):
    STANDARD = "standard"   # Ascendant-based (normal)
    CHANDRA = "chandra"     # Moon-based (failover for uncertain birth time)


# ──────────────────────────────────────────────────────────────────
# Dasha Level
# ──────────────────────────────────────────────────────────────────
class DashaLevel(str, Enum):
    MAHADASHA = "mahadasha"
    ANTARDASHA = "antardasha"
    PRATYANTARDASHA = "pratyantardasha"


# ──────────────────────────────────────────────────────────────────
# Dignity classification
# ──────────────────────────────────────────────────────────────────
class Dignity(str, Enum):
    EXALTED = "exalted"
    MOOLATRIKONA = "moolatrikona"
    OWN = "own"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    ENEMY = "enemy"
    DEBILITATED = "debilitated"


# Dignity to numeric score mapping
DIGNITY_SCORE: dict[Dignity, float] = {
    Dignity.EXALTED: 1.0,
    Dignity.MOOLATRIKONA: 0.85,
    Dignity.OWN: 0.75,
    Dignity.FRIENDLY: 0.5,
    Dignity.NEUTRAL: 0.25,
    Dignity.ENEMY: 0.125,
    Dignity.DEBILITATED: 0.0,
}
