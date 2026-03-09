# Jyotish AI — Solution Overview

A Vedic Astrology Prediction Engine that computes birth charts, scores life-event predictions through a three-gate system, and delivers AI-narrated results.

## Architecture at a Glance

```
User → React Frontend → FastAPI Backend
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               Compute   Predict   Narrate
               (Engine)  (3-Gate)  (Claude AI)
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                     Deliver & Store
                   (API / WhatsApp / DB)
```

## Key Layers

| Layer | What It Does |
|-------|-------------|
| **Engine** | Computes birth charts using Swiss Ephemeris — planet positions, houses, dashas, ashtakavarga, yogas, doshas |
| **Prediction** | Runs a three-gate scoring system: (1) Birth chart promise, (2) Active dasha connection, (3) Transit window detection |
| **Narration** | Sends pre-computed scores to Claude AI to generate human-readable prediction text |
| **Delivery** | Dispatches results via API response or WhatsApp (OpenClaw) |
| **Engagement** | Weekly lagna-based transit insights delivered on a cron schedule |

## How It Works

1. **User enters birth data** — date, time, place (lat/lon)
2. **Engine computes the birth chart** — all positions stored as integer arc-seconds for precision
3. **Three-gate prediction** — scores promise (birth chart strength), dasha (active time-lord relevance), and transit (planetary movement windows) for 5 event types: marriage, career, child, property, health
4. **AI narrates the result** — Claude converts scores into a readable paragraph
5. **Result is delivered** — returned via API and/or sent to WhatsApp; stored in SQLite

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), SQLite
- **Astro Engine:** PySwissEph (Swiss Ephemeris)
- **AI:** Anthropic Claude API (narration)
- **Frontend:** React 18, TypeScript, Vite
- **Auth:** JWT + bcrypt
- **Delivery:** WhatsApp via OpenClaw API, direct API response

## API & Frontend

- **API** — RESTful endpoints under `/api/v1` (auth, predictions, charts, kundli, engagement, delivery)
- **Frontend** — SPA with pages for login, prediction, chart visualization (North/South Indian styles), kundli, and history
