# Feature Roadmap — All Calculators & Tools

**Date:** 2026-04-23
**Current State:** 10 features built, 50+ features identified for implementation
**Engine:** 3-gate Vedic astrology engine with Swiss Ephemeris

---

## How to Read This Document

Each feature is marked with its **engine readiness:**
- ✅ **ENGINE READY** — Our astrology engine already computes the underlying data. Just need a new API endpoint + formatting.
- ⚠️ **PARTIAL** — Engine computes some data, but needs additional logic.
- 🆕 **NEW BUILD** — Needs new computation logic (not in current engine).
- 🤖 **AI POWERED** — Uses Claude API for narration/generation.

---

## TIER 1 — Quick Wins (1-2 days each)

These use data our engine **already computes**. Just need a dedicated API endpoint.

| # | Feature | What It Does | Engine Status | Effort | User Value |
|---|---|---|---|---|---|
| 1 | **Moon Sign (Rashi) Calculator** | Find your Moon sign from birth date/time | ✅ ENGINE READY — Moon position computed in chart | 4 hours | High |
| 2 | **Sun Sign Calculator** | Find your Vedic Sun sign | ✅ ENGINE READY — Sun position computed in chart | 4 hours | High |
| 3 | **Rising Sign (Lagna) Calculator** | Find your Ascendant sign | ✅ ENGINE READY — Lagna computed in chart | 4 hours | High |
| 4 | **Nakshatra Calculator** | Find your birth star (27 nakshatras) | ✅ ENGINE READY — Moon's nakshatra position computed | 4 hours | High |
| 5 | **Dasha Calculator** | Show current + upcoming Mahadasha/Antardasha | ✅ ENGINE READY — Full dasha tree already computed | 1 day | Very High |
| 6 | **Mangal Dosha Calculator** | Check if Mars causes Mangal Dosha | ✅ ENGINE READY — Mangal dosha detection exists | 1 day | Very High |
| 7 | **Kaal Sarpa Dosha Calculator** | Check if all planets between Rahu-Ketu | ✅ ENGINE READY — Kaal Sarpa detection exists | 4 hours | High |
| 8 | **Yoga Calculator** | List all yogas present in birth chart | ✅ ENGINE READY — 10 yogas already detected | 1 day | High |
| 9 | **Planetary Position Report** | All 9 planets with sign, degree, dignity | ✅ ENGINE READY — All computed in chart | 4 hours | Medium |
| 10 | **Ashtakavarga Report** | BAV + SAV scores for all 12 signs | ✅ ENGINE READY — Full ashtakavarga computed | 1 day | Medium |

**TIER 1 Total Effort: ~7-8 days for all 10 features**

---

## TIER 2 — High Value Features (3-7 days each)

These need some new logic but build on existing engine capabilities.

| # | Feature | What It Does | Engine Status | Effort | User Value |
|---|---|---|---|---|---|
| 11 | **Kundli Matching (Ashtakoota)** | 36-point gun milan for marriage compatibility | ⚠️ PARTIAL — Need 8 kuta matching algorithm (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakut, Nadi) | 1-2 weeks | **Very High** (biggest revenue driver) |
| 12 | **Daily Horoscope (12 signs)** | Today's prediction for each zodiac sign | ⚠️ PARTIAL — Transit engine exists + 🤖 Claude narration | 2-3 days | **Very High** (daily engagement) |
| 13 | **Sade Sati Calculator** | Check Saturn's 7.5-year transit over Moon sign | ⚠️ PARTIAL — Saturn position + Moon sign computed, need transit window logic | 3 days | High |
| 14 | **Panchang** | Daily tithi, nakshatra, yoga, karana, sunrise/sunset | 🆕 NEW BUILD — Need tithi/karana/panchang yoga computation from ephemeris | 1 week | **Very High** (daily usage) |
| 15 | **Transit Report** | Current Jupiter/Saturn transits mapped to birth chart | ✅ ENGINE READY — Transit computation exists, need better formatting | 3 days | High |
| 16 | **Numerology Calculator** | Life path number, destiny number, soul number from birth date + name | 🆕 NEW BUILD — Simple arithmetic on digits, no astrology engine needed | 2 days | High |
| 17 | **Love/Compatibility Calculator** | Compatibility score between two people | ⚠️ PARTIAL — Need to compare two charts (Moon signs, 7th lords, Venus positions) | 5 days | High |
| 18 | **Kundli PDF Report** | Downloadable birth chart analysis as PDF | ✅ ENGINE READY — All data exists, need PDF generation (ReportLab/WeasyPrint) | 1 week | **Very High** (premium feature) |
| 19 | **Muhurat Finder** | Find auspicious date/time for marriage, business, travel, etc. | ⚠️ PARTIAL — Transit + panchang needed. Must check tithi, nakshatra, yoga for favorable windows | 1-2 weeks | High |
| 20 | **Monthly Horoscope** | Month-ahead prediction per sign | ⚠️ PARTIAL — Transit analysis + 🤖 Claude narration | 3 days | High |

**TIER 2 Total Effort: ~6-8 weeks for all 10 features**

---

## TIER 3 — Extended Calculators (1-3 days each)

These are additional tools that astrology apps typically offer.

| # | Feature | What It Does | Engine Status | Effort | User Value |
|---|---|---|---|---|---|
| 21 | **Nadi Dosha Calculator** | Check Nadi compatibility for marriage | ✅ ENGINE READY — Nadi dosha detection exists | 4 hours | High |
| 22 | **Bhakut Dosha Calculator** | Check Bhakut (sign-pair) compatibility | ⚠️ PARTIAL — Moon signs needed for both partners | 1 day | Medium |
| 23 | **Ayanamsha Calculator** | Show positions in different ayanamsha systems (Lahiri, Raman, KP) | ✅ ENGINE READY — Ayanamsha configurable | 1 day | Low |
| 24 | **Varshphal (Annual Chart)** | Solar return chart for current year | 🆕 NEW BUILD — Need solar return computation (Sun returns to natal position) | 1 week | Medium |
| 25 | **D-9 Navamsha Analysis** | Detailed navamsha chart with interpretation | ✅ ENGINE READY — Navamsha computed | 2 days | Medium |
| 26 | **D-10 Dashamsha Analysis** | Career-specific divisional chart | 🆕 NEW BUILD — Need D-10 computation logic | 3 days | Medium |
| 27 | **Gem Recommendation** | Suggest gemstones based on weak planets | ⚠️ PARTIAL — Planet dignity known, need gem-planet mapping | 2 days | **High** (monetizable) |
| 28 | **Rudraksha Recommendation** | Suggest rudraksha based on birth chart | 🆕 NEW BUILD — Need rudraksha-planet mapping | 1 day | Medium |
| 29 | **Ishta Devata Calculator** | Determine personal deity from Atmakaraka | ⚠️ PARTIAL — Planet positions known, need Atmakaraka + deity mapping | 2 days | Medium |
| 30 | **Yearly Horoscope** | Year-ahead prediction per sign | ⚠️ PARTIAL — Transit analysis + 🤖 Claude narration | 3 days | High |

**TIER 3 Total Effort: ~3-4 weeks for all 10 features**

---

## TIER 4 — Advanced & Unique Features (1-2 weeks each)

These differentiate from competitors.

| # | Feature | What It Does | Engine Status | Effort | User Value |
|---|---|---|---|---|---|
| 31 | **AI Astrologer Chat** | Conversational AI answering birth chart questions | 🤖 AI POWERED — Claude API with chart context | 1-2 weeks | **Very High** |
| 32 | **Event Timeline** | Visual timeline: "When will marriage/career/child happen?" | ✅ ENGINE READY — Our 3-gate prediction is this | 1 week | **Very High** |
| 33 | **Remedies Engine** | Suggest mantras, gems, donations for weak areas | 🆕 NEW BUILD — Need remedy-planet-house mapping | 2 weeks | **High** (monetizable) |
| 34 | **KP (Krishnamurti) System** | Sub-lord based predictions (different from Parashari) | 🆕 NEW BUILD — Different computation system | 3-4 weeks | Medium |
| 35 | **Lal Kitab Report** | Lal Kitab chart with remedies | 🆕 NEW BUILD — Different chart system + remedy database | 3-4 weeks | Medium |
| 36 | **Prashna Kundli** | Horary astrology — chart for the question time | ⚠️ PARTIAL — Chart computation works for any time, need Prashna-specific interpretation | 1-2 weeks | Medium |
| 37 | **Marriage Timing Prediction** | When will marriage happen? (year/month range) | ✅ ENGINE READY — This IS our 3-gate system for marriage | 1 week | **Very High** |
| 38 | **Career Timing Prediction** | When will career breakthrough happen? | ✅ ENGINE READY — This IS our 3-gate system for career | 1 week | **Very High** |
| 39 | **Manglik Matching** | Compare two charts for Mangal Dosha compatibility | ⚠️ PARTIAL — Mangal detection exists for both, need comparison logic | 3 days | High |
| 40 | **Baby Name Suggestion** | Suggest names based on Moon nakshatra | 🆕 NEW BUILD — Need nakshatra-syllable mapping + name database | 1-2 weeks | High |

**TIER 4 Total Effort: ~10-14 weeks for all 10 features**

---

## TIER 5 — Engagement & Content

| # | Feature | What It Does | Engine Status | Effort | User Value |
|---|---|---|---|---|---|
| 41 | **Weekly Horoscope** | Weekly prediction per sign | ✅ ALREADY BUILT | Done | High |
| 42 | **Push Notifications** | "Your favorable period starts tomorrow" | ⚠️ PARTIAL — Transit data exists, need push infra | 1 week | High |
| 43 | **Festival/Vrat Calendar** | Hindu festival dates with significance | 🆕 NEW BUILD — Need festival date computation from panchang | 1 week | Medium |
| 44 | **Retrograde Alerts** | Notify when Mercury/Saturn/Jupiter go retrograde | ✅ ENGINE READY — Planet positions tracked, need retrograde detection | 2 days | Medium |
| 45 | **Eclipse Report** | Solar/lunar eclipse dates + chart impact | 🆕 NEW BUILD — Ephemeris can compute, need eclipse logic | 3 days | Medium |

---

## TIER 6 — Utility Converters

| # | Feature | What It Does | Engine Status | Effort | User Value |
|---|---|---|---|---|---|
| 46 | **Ghati to Hour Converter** | Convert Hindu time units to standard | 🆕 NEW BUILD — Simple math formula | 2 hours | Low |
| 47 | **Naam Rashi Calculator** | Find Rashi from name (when birth time unknown) | 🆕 NEW BUILD — First-letter to sign mapping | 4 hours | Medium |
| 48 | **Chinese Zodiac Calculator** | Chinese zodiac animal from birth year | 🆕 NEW BUILD — Simple year modulo calculation | 2 hours | Low |
| 49 | **Yantra Calculator** | Recommend yantra based on chart | 🆕 NEW BUILD — Planet-yantra mapping | 4 hours | Low |
| 50 | **Friendship Calculator** | Fun compatibility between friends | 🆕 NEW BUILD — Moon sign + nakshatra comparison | 4 hours | Low |

---

## SUMMARY — Complete Feature Roadmap

### By Effort

| Tier | Features | Effort | Revenue Impact |
|---|---|---|---|
| **Tier 1** (Quick Wins) | 10 features | ~7-8 days | Medium — builds credibility |
| **Tier 2** (High Value) | 10 features | ~6-8 weeks | **High — revenue drivers** |
| **Tier 3** (Extended) | 10 features | ~3-4 weeks | Medium |
| **Tier 4** (Advanced) | 10 features | ~10-14 weeks | **High — differentiation** |
| **Tier 5** (Engagement) | 5 features | ~2-3 weeks | Medium — retention |
| **Tier 6** (Utility) | 5 features | ~2 days | Low |
| **TOTAL** | **50 features** | **~25-35 weeks** | |

### By Engine Readiness

| Status | Count | Meaning |
|---|---|---|
| ✅ ENGINE READY | 20 | Data already computed, just need endpoint |
| ⚠️ PARTIAL | 14 | Some logic exists, need additions |
| 🆕 NEW BUILD | 13 | New computation needed |
| 🤖 AI POWERED | 3 | Uses Claude API |
| **TOTAL** | **50** | |

### Top 10 Priority Features (Highest Impact)

| Rank | Feature | Why It's #1 Priority |
|---|---|---|
| 1 | **Kundli Matching** | #1 revenue driver in Indian astrology. Every marriage needs it. |
| 2 | **Daily Horoscope** | Daily engagement — brings users back every day. |
| 3 | **Event Timeline (Marriage/Career)** | Already built (3-gate system). Our core differentiator. |
| 4 | **Mangal Dosha Calculator** | Every marriage involves Mangal check. High concern. |
| 5 | **Dasha Calculator** | Users want to know "what period am I in?" Very popular query. |
| 6 | **Panchang** | Daily Hindu calendar. Used by millions daily. |
| 7 | **Kundli PDF Report** | Premium feature. Downloadable, shareable, printable. |
| 8 | **AI Astrologer Chat** | Differentiator — conversational AI with chart context. |
| 9 | **Gem Recommendation** | Monetizable — sell gemstones based on recommendations. |
| 10 | **Sade Sati Calculator** | Saturn's 7.5-year transit — high anxiety, high search volume. |

### Already Built (What We Have Today)

| Feature | Endpoint | Status |
|---|---|---|
| Kundli Generator | `POST /api/v1/kundli/compute` | ✅ Live |
| Birth Chart (full) | `GET /api/v1/charts/user/{id}` | ✅ Live |
| Event Prediction (5 types) | `POST /api/v1/predictions` | ✅ Live |
| Weekly Transit Insights | `GET /api/v1/engagement/weekly` | ✅ Live |
| User Registration + Auth | `POST /api/v1/auth/register` | ✅ Live |
| Life Event Recording | `POST /api/v1/events` | ✅ Live |
| WhatsApp Delivery | `POST /api/v1/webhook/whatsapp` | ✅ Live |
| Delivery Tracking | `GET /api/v1/delivery/.../status` | ✅ Live |
| Health Check | `GET /api/v1/health` | ✅ Live |
| AI Narration (Claude) | Built into prediction flow | ✅ Live |

---

## Implementation Recommendation

### Phase 1 — Launch MVP (2-3 weeks)
Build Tier 1 (10 quick-win calculators) + deploy to production. Gets you a competitive astrology app with 20+ features.

### Phase 2 — Revenue Features (4-6 weeks)
Add Kundli Matching + Daily Horoscope + Kundli PDF + Gem Recommendation. These are the money-makers.

### Phase 3 — Differentiation (6-10 weeks)
Add AI Astrologer Chat + Panchang + Muhurat Finder + Remedies Engine. These set you apart from AstroTalk/AstroSage.

### Phase 4 — Complete Platform (10-14 weeks)
Add remaining Tier 3-6 features to match AstroTalk's full feature set.

**Total time to feature parity with AstroTalk: ~25-35 weeks (~6-8 months)**
**But you can launch a competitive MVP in 2-3 weeks with what you have + Tier 1.**

---

## External Dependency Analysis

### Can We Build Everything Without External Input?

**YES — 90% of features (45 out of 50) need ZERO external input.**

### Category 1: Fully Self-Contained (35 features — 70%)

Built entirely from our engine + Python code. No external data, no API keys, no third-party services. Swiss Ephemeris computes everything.

| # | Feature | Why It's Self-Contained |
|---|---|---|
| 1 | Moon Sign Calculator | Moon position from Swiss Ephemeris — already computed |
| 2 | Sun Sign Calculator | Sun position from Swiss Ephemeris — already computed |
| 3 | Rising Sign Calculator | Lagna from Swiss Ephemeris — already computed |
| 4 | Nakshatra Calculator | Moon degree → nakshatra mapping — math formula |
| 5 | Dasha Calculator | Vimshottari dasha tree — already computed |
| 6 | Mangal Dosha Calculator | Mars position check — already computed |
| 7 | Kaal Sarpa Dosha Calculator | Rahu-Ketu axis check — already computed |
| 8 | Yoga Calculator | 10 yogas — already detected |
| 9 | Planetary Position Report | All 9 planets — already computed |
| 10 | Ashtakavarga Report | BAV/SAV — already computed |
| 13 | Sade Sati Calculator | Saturn transit over Moon sign — ephemeris computes |
| 14 | Panchang | Tithi, Nakshatra, Yoga, Karana — all from Sun-Moon positions via ephemeris |
| 15 | Transit Report | Jupiter/Saturn transits — already computed in Gate 3 |
| 16 | Numerology Calculator | Pure math on birth date digits — no astrology engine needed |
| 17 | Love/Compatibility Calculator | Compare two charts — both computable from birth data |
| 18 | Kundli PDF Report | All data exists — need ReportLab Python library (free, no API) |
| 19 | Muhurat Finder | Panchang + transit computation — all from ephemeris |
| 21 | Nadi Dosha Calculator | Nakshatra comparison — already detected |
| 22 | Bhakut Dosha Calculator | Moon sign pair check — fixed rule table |
| 23 | Ayanamsha Calculator | Swiss Ephemeris supports multiple ayanamshas |
| 24 | Varshphal (Annual Chart) | Solar return = Sun reaches natal degree — ephemeris computes |
| 25 | D-9 Navamsha Analysis | Already computed in engine |
| 26 | D-10 Dashamsha Analysis | Division chart = same math as D-9 with different divisor |
| 32 | Event Timeline | This IS our 3-gate prediction system — already built |
| 34 | KP System | Sub-lord computation from Swiss Ephemeris |
| 36 | Prashna Kundli | Chart for current moment — same engine, use 'now' as birth time |
| 37 | Marriage Timing | Already built — 3-gate system with event_type=marriage |
| 38 | Career Timing | Already built — 3-gate system with event_type=career |
| 39 | Manglik Matching | Compare Mangal dosha of two charts — both computable |
| 41 | Weekly Horoscope | Already built and live |
| 44 | Retrograde Alerts | Planet velocity from Swiss Ephemeris — negative = retrograde |
| 45 | Eclipse Report | Swiss Ephemeris has eclipse computation functions |
| 46 | Ghati to Hour Converter | Simple math: 1 ghati = 24 minutes |
| 48 | Chinese Zodiac Calculator | birth_year % 12 → animal. Pure math |
| 50 | Friendship Calculator | Moon sign + nakshatra comparison |

### Category 2: Need Fixed Knowledge Data (10 features — 20%)

Need lookup tables from Vedic texts. These are **permanent rules that never change** — same for thousands of years. Can be hardcoded as JSON/Python dicts. No external data source or API needed.

| # | Feature | Fixed Data Needed | Size |
|---|---|---|---|
| 11 | Kundli Matching (Ashtakoota) | 8 kuta scoring rules (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakut, Nadi) | ~200 lines JSON |
| 27 | Gem Recommendation | Planet → Gemstone mapping (Sun→Ruby, Moon→Pearl, Mars→Coral, etc.) | 9 entries |
| 28 | Rudraksha Recommendation | Planet → Rudraksha mapping (Sun→1 mukhi, Moon→2 mukhi, etc.) | 9 entries |
| 29 | Ishta Devata Calculator | Atmakaraka → Deity mapping (from Jaimini Sutras) | 9 entries |
| 33 | Remedies Engine | Remedy database: mantras, donations, fasting per planet/house | ~100 entries |
| 35 | Lal Kitab Report | Lal Kitab rules + remedy database | ~500 lines |
| 40 | Baby Name Suggestion | Nakshatra → starting syllable mapping + name database | 108 syllables |
| 43 | Festival Calendar | Hindu festival computation rules from panchang | ~30 rules |
| 47 | Naam Rashi Calculator | First letter → sign mapping | 26 entries |
| 49 | Yantra Calculator | Planet → Yantra mapping | 9 entries |

**All of this is standard Vedic astrology textbook knowledge. No external lookup needed.**

### Category 3: Need Claude API Key (4 features — 8%)

Need Anthropic Claude API key for AI-generated text. **All 4 features work WITHOUT the API key** using rule-based templates — the API just makes the text more natural and engaging.

| # | Feature | With API Key | Without API Key |
|---|---|---|---|
| 12 | Daily Horoscope (12 signs) | AI-generated personalized content | Template-based: "Transit of Jupiter in your 7th house brings..." |
| 20 | Monthly Horoscope | AI narrative for the month ahead | Template with transit data filled in |
| 30 | Yearly Horoscope | AI narrative for the year ahead | Template with major transit data |
| 31 | AI Astrologer Chat | Conversational AI answering chart questions | Not available without API (skip for MVP) |

### Category 4: Need External Infrastructure (1 feature — 2%)

| # | Feature | External Service Needed | Can Skip for MVP? |
|---|---|---|---|
| 42 | Push Notifications | Firebase Cloud Messaging or OneSignal | Yes — use email/WhatsApp instead |

---

## Final Summary

```
┌─────────────────────────────────────────────────────┐
│           50 FEATURES — DEPENDENCY MAP              │
│                                                     │
│   ████████████████████████████████████░░░░░░░░░░    │
│   35 Self-Contained    10 Fixed Data   4 API  1 Ext │
│        (70%)              (20%)        (8%)   (2%)  │
│                                                     │
│   ██████████████████████████████████████████████░░   │
│   45 features = NO external input needed (90%)      │
│                                                     │
│   ████████████████████████████████████████████████   │
│   49 features work without any paid service (98%)   │
│                                                     │
│   Only AI Chat (#31) truly requires Claude API      │
│   Everything else has a free fallback               │
└─────────────────────────────────────────────────────┘
```

| Question | Answer |
|---|---|
| Can we build all 50 features? | **Yes** |
| How many need external input? | **5 (10%)** — and 4 of those work without it |
| How many need paid services? | **1 (2%)** — AI Chat needs Claude API. Rest are free. |
| What do I need from you? | **Only: which features to build first** |
| Biggest dependency? | **Swiss Ephemeris** (already installed and working) |
