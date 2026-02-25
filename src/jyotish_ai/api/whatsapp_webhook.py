"""WhatsApp inbound webhook — receives messages from OpenClaw and handles
conversational registration, Kundli retrieval, and predictions.

Commands for registered users:
  - "kundli" / "chart" → compute & send birth chart summary
  - "predict <event>" → run prediction for an event type
  - "help" → list available commands
  - anything else → show menu

Registration flow for new users:
  1. User sends any message → Bot checks phone
  2. If not registered → conversational onboarding:
     Name → Birth date → Birth time → Birth place → Confirm
  3. Creates user in DB with WhatsApp opt-in
"""
from __future__ import annotations

import logging
from datetime import date, time as dt_time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.api.deps import get_db_session, get_user_repo
from jyotish_ai.config import settings
from jyotish_ai.persistence.models import User
from jyotish_ai.persistence.repositories import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# ── In-memory conversation state ────────────────────────────
_conversations: dict[str, dict] = {}

PROMPTS = {
    "welcome": (
        "Namaste! Welcome to *Jyotish AI* - Vedic Astrology Predictions.\n\n"
        "Let's get you registered. What is your *full name*?"
    ),
    "birth_date": "Thank you, {name}! Now, please share your *date of birth* (DD-MM-YYYY format).",
    "birth_time": "Got it! What is your *birth time*? (HH:MM format, 24hr)\nIf unknown, type *skip*.",
    "birth_place": "Now, please share your *birth place* (city name).",
    "confirm": (
        "Here's your registration summary:\n\n"
        "Name: *{name}*\n"
        "Birth Date: *{birth_date}*\n"
        "Birth Time: *{birth_time}*\n"
        "Birth Place: *{birth_place}*\n\n"
        "Type *yes* to confirm or *no* to start over."
    ),
    "success": (
        "Registration complete! Your Jyotish AI account is ready.\n\n"
        "Your User ID: *{user_id}*\n"
        "Delivery: WhatsApp enabled\n\n"
        "Type *kundli* to see your birth chart.\n"
        "Type *help* for all commands."
    ),
    "menu": (
        "Namaste *{name}*! Here's what I can do:\n\n"
        "Type *kundli* — View your birth chart\n"
        "Type *predict marriage* — Marriage prediction\n"
        "Type *predict career* — Career prediction\n"
        "Type *predict child* — Child prediction\n"
        "Type *predict property* — Property prediction\n"
        "Type *predict health* — Health prediction\n"
        "Type *help* — Show this menu"
    ),
    "restart": "No problem! Let's start over. What is your *full name*?",
    "error_date": "Invalid date format. Please use *DD-MM-YYYY* (e.g., 15-05-1990).",
    "error_time": "Invalid time format. Please use *HH:MM* 24-hour format (e.g., 09:30) or type *skip*.",
}

VALID_EVENTS = {"marriage", "career", "child", "property", "health"}


def _parse_date(text: str) -> Optional[date]:
    text = text.strip().replace("/", "-")
    try:
        parts = text.split("-")
        if len(parts) != 3:
            return None
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def _parse_time(text: str) -> Optional[dt_time]:
    text = text.strip()
    if text.lower() == "skip":
        return None
    try:
        parts = text.split(":")
        return dt_time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return None


# ── Kundli Formatter ────────────────────────────────────────

def _format_kundli_whatsapp(chart) -> str:
    """Format a BirthChart domain object as a WhatsApp-friendly text message."""
    from jyotish_ai.domain.models import BirthChart

    lines = []
    lines.append("*Your Kundli (Birth Chart)*")
    lines.append(f"Ascendant (Lagna): *{chart.ascendant_sign.name}*")
    lines.append(f"Lagna Mode: {chart.lagna_mode.value}")
    lines.append("")

    # Planet positions table
    lines.append("*Planetary Positions:*")
    lines.append("```")
    lines.append(f"{'Planet':<10} {'Sign':<12} {'House':>5} {'Deg':>7} {'Dignity':<12}")
    lines.append("-" * 48)
    for p in chart.planets:
        deg_str = f"{p.sign_degrees:.1f}"
        retro = " (R)" if p.is_retrograde else ""
        lines.append(
            f"{p.planet.value:<10} {p.sign.name:<12} {p.house:>5} {deg_str:>7} {p.dignity.value}{retro}"
        )
    lines.append("```")
    lines.append("")

    # Houses
    lines.append("*House Cusps:*")
    lines.append("```")
    for h in chart.houses:
        lines.append(f"House {h.house_number:>2}: {h.sign.name:<12} ({h.span_degrees:.1f} deg)")
    lines.append("```")
    lines.append("")

    # Current Dasha
    if chart.dasha_tree:
        from datetime import date as dt_date
        today = dt_date.today()
        active_md = None
        active_ad = None
        for d in chart.dasha_tree:
            if d.level.value == "mahadasha" and d.start_date <= today <= d.end_date:
                active_md = d
            elif d.level.value == "antardasha" and d.start_date <= today <= d.end_date:
                active_ad = d

        lines.append("*Current Dasha Period:*")
        if active_md:
            lines.append(
                f"Mahadasha: *{active_md.planet.value}* "
                f"({active_md.start_date} to {active_md.end_date})"
            )
        if active_ad:
            lines.append(
                f"Antardasha: *{active_ad.planet.value}* "
                f"({active_ad.start_date} to {active_ad.end_date})"
            )
        if not active_md and not active_ad:
            lines.append("(Dasha period data available)")
        lines.append("")

    # Ashtakavarga SAV highlights
    if chart.ashtakavarga and chart.ashtakavarga.sav:
        lines.append("*Ashtakavarga (SAV) Top Signs:*")
        sav = chart.ashtakavarga.sav
        sorted_sav = sorted(sav.items(), key=lambda x: x[1], reverse=True)[:4]
        for sign_name, score in sorted_sav:
            lines.append(f"  {sign_name}: {score} pts")
        lines.append("")

    # Quality flags
    qf = chart.quality_flags
    flags = []
    if qf.birth_time_tier:
        flags.append(f"Birth Time: Tier {qf.birth_time_tier.value}")
    if qf.lagna_mode:
        flags.append(f"Lagna: {qf.lagna_mode.value}")
    if qf.placidus_distorted:
        flags.append("Placidus distorted (Equal House used)")
    if flags:
        lines.append("*Quality Notes:*")
        for f in flags:
            lines.append(f"  {f}")
        lines.append("")

    lines.append("Type *predict marriage* (or career/child/property/health) for predictions.")

    full = "\n".join(lines)
    # WhatsApp has a ~4096 char limit
    if len(full) > 4000:
        full = full[:3950] + "\n\n[Message truncated]"
    return full


# ── Prediction Formatter ────────────────────────────────────

def _format_prediction_whatsapp(result, event_type: str) -> str:
    """Format a PredictionResult as WhatsApp text."""
    lines = []
    lines.append(f"*Prediction: {event_type.title()}*")
    lines.append("")

    # Confidence
    conf = result.confidence_level.value if hasattr(result.confidence_level, 'value') else result.confidence_level
    score = result.convergence_score
    lines.append(f"Convergence Score: *{score:.2f} / 3.00*")
    lines.append(f"Confidence: *{conf.upper()}*")
    lines.append("")

    # Gate scores
    lines.append("*Gate Scores:*")
    lines.append(f"  Gate 1 (Promise): {result.gate1.score:.2f}")
    lines.append(f"  Gate 2 (Dasha): {result.gate2.score:.2f}")
    lines.append(f"  Gate 3 (Transit): {result.gate3.score:.2f}")
    lines.append("")

    # Timeline
    if result.timeline and result.timeline.get("active_months"):
        lines.append("*Favorable Transit Months:*")
        months = result.timeline["active_months"][:6]
        lines.append("  " + ", ".join(months))
        if result.timeline.get("peak_month"):
            lines.append(f"  Peak: *{result.timeline['peak_month']}*")
        lines.append("")

    # Narration
    if result.narration_text:
        lines.append("*Analysis:*")
        narr = result.narration_text
        if len(narr) > 1500:
            narr = narr[:1450] + "..."
        lines.append(narr)

    return "\n".join(lines)


# ── Webhook Verification (GET) ──────────────────────────────

@router.get("/whatsapp")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification handshake."""
    if mode == "subscribe" and token == settings.openclaw_webhook_verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return int(challenge) if challenge else "OK"
    raise HTTPException(status_code=403, detail="Verification failed")


# ── Webhook Message Handler (POST) ──────────────────────────

@router.post("/whatsapp")
async def receive_whatsapp_message(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Receive inbound WhatsApp messages and route to appropriate handler."""
    body = await request.json()
    logger.debug("WhatsApp webhook payload: %s", body)

    message_data = _extract_message(body)
    if not message_data:
        return {"status": "no_message"}

    phone = message_data["phone"]
    text = message_data["text"].strip()
    text_lower = text.lower()

    logger.info("WhatsApp message from %s: %s", phone, text[:50])

    # Check if user already exists with this phone
    existing_user = await _find_user_by_phone(user_repo, phone)

    # ── Registered user: handle commands ──
    if existing_user and phone not in _conversations:
        reply, action = await _handle_registered_user(
            existing_user, text, text_lower, session
        )
        await _send_reply(phone, reply)
        return {"status": action, "user_id": existing_user.id}

    # ── Unregistered user: registration conversation ──
    reply, user_id = await _handle_conversation(phone, text, session, user_repo)
    await _send_reply(phone, reply)

    result = {"status": "replied", "phone": phone}
    if user_id:
        result["user_id"] = user_id
        result["registration"] = "complete"
    return result


async def _handle_registered_user(
    user: User,
    text: str,
    text_lower: str,
    session: AsyncSession,
) -> tuple[str, str]:
    """Handle commands from an already-registered user.

    Returns (reply_text, action_name).
    """

    # ── KUNDLI / CHART ──
    if text_lower in ("kundli", "chart", "birth chart", "janam kundli", "horoscope"):
        try:
            from jyotish_ai.services.chart_service import ChartService
            chart_svc = ChartService(session)
            chart = await chart_svc.get_or_compute_chart(user)
            reply = _format_kundli_whatsapp(chart)
            return reply, "kundli_sent"
        except Exception as e:
            logger.exception("Kundli computation failed for user %d", user.id)
            return (
                f"Sorry, could not compute your Kundli: {str(e)[:100]}\n\n"
                "Please ensure your birth data is complete (date, time, place).",
                "kundli_error",
            )

    # ── PREDICT <event> ──
    if text_lower.startswith("predict"):
        parts = text_lower.split(None, 1)
        event_type = parts[1].strip() if len(parts) > 1 else ""

        if event_type not in VALID_EVENTS:
            return (
                f"Unknown event type: *{event_type or '(none)'}*\n\n"
                "Available: *marriage*, *career*, *child*, *property*, *health*\n"
                "Example: *predict marriage*",
                "predict_invalid",
            )

        try:
            from jyotish_ai.services.orchestrator import PredictionOrchestrator
            from jyotish_ai.domain.types import EventType
            orch = PredictionOrchestrator(session)
            result, pred_id = await orch.run_prediction(
                user=user,
                event_type=EventType(event_type),
                query_date=date.today(),
                is_retrospective=False,
            )
            reply = _format_prediction_whatsapp(result, event_type)
            return reply, "prediction_sent"
        except Exception as e:
            logger.exception("Prediction failed for user %d", user.id)
            return (
                f"Sorry, prediction failed: {str(e)[:150]}\n\n"
                "Type *help* for available commands.",
                "prediction_error",
            )

    # ── HELP / MENU ──
    if text_lower in ("help", "menu", "commands", "options"):
        return PROMPTS["menu"].format(name=user.name), "help"

    # ── Default: show menu ──
    return PROMPTS["menu"].format(name=user.name), "menu"


def _extract_message(body: dict) -> Optional[dict]:
    """Extract phone number and text from OpenClaw/Meta webhook payload."""
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        phone = msg.get("from", "")
        text = ""

        if msg.get("type") == "text":
            text = msg.get("text", {}).get("body", "")
        elif msg.get("type") == "interactive":
            interactive = msg.get("interactive", {})
            text = (
                interactive.get("button_reply", {}).get("title", "")
                or interactive.get("list_reply", {}).get("title", "")
            )

        if not phone or not text:
            return None

        return {"phone": phone, "text": text}
    except (KeyError, IndexError):
        return None


async def _find_user_by_phone(user_repo: UserRepository, phone: str) -> Optional[User]:
    """Look up user by phone number (with or without + prefix)."""
    from sqlalchemy import select
    from jyotish_ai.persistence.models import User as UserModel

    stmt = select(UserModel).where(UserModel.phone_number == phone).limit(1)
    result = await user_repo.session.execute(stmt)
    user = result.scalars().first()
    if user:
        return user

    alt = f"+{phone}" if not phone.startswith("+") else phone[1:]
    stmt = select(UserModel).where(UserModel.phone_number == alt).limit(1)
    result = await user_repo.session.execute(stmt)
    return result.scalars().first()


async def _handle_conversation(
    phone: str,
    text: str,
    session: AsyncSession,
    user_repo: UserRepository,
) -> tuple[str, Optional[int]]:
    """Process a message in the registration conversation."""
    if phone not in _conversations:
        _conversations[phone] = {"step": "name", "data": {"phone": phone}}
        return PROMPTS["welcome"], None

    conv = _conversations[phone]
    step = conv["step"]

    if step == "name":
        conv["data"]["name"] = text
        conv["step"] = "birth_date"
        return PROMPTS["birth_date"].format(name=text), None

    elif step == "birth_date":
        parsed = _parse_date(text)
        if not parsed:
            return PROMPTS["error_date"], None
        conv["data"]["birth_date"] = parsed
        conv["step"] = "birth_time"
        return PROMPTS["birth_time"], None

    elif step == "birth_time":
        if text.lower() == "skip":
            conv["data"]["birth_time"] = None
            conv["step"] = "birth_place"
            return PROMPTS["birth_place"], None

        parsed = _parse_time(text)
        if parsed is None and text.lower() != "skip":
            return PROMPTS["error_time"], None
        conv["data"]["birth_time"] = parsed
        conv["step"] = "birth_place"
        return PROMPTS["birth_place"], None

    elif step == "birth_place":
        conv["data"]["birth_place"] = text
        conv["step"] = "confirm"
        return PROMPTS["confirm"].format(
            name=conv["data"]["name"],
            birth_date=str(conv["data"]["birth_date"]),
            birth_time=str(conv["data"].get("birth_time") or "Not provided"),
            birth_place=conv["data"]["birth_place"],
        ), None

    elif step == "confirm":
        if text.lower() in ("yes", "y", "ha", "haan"):
            data = conv["data"]
            phone_number = data["phone"]
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"

            user = User(
                name=data["name"],
                birth_date=data["birth_date"],
                birth_time=data.get("birth_time"),
                birth_place=data.get("birth_place", "Not specified"),
                latitude=28.6,
                longitude=77.2,
                timezone_offset=5.5,
                birth_time_tier=2,
                phone_number=phone_number,
                delivery_preference="whatsapp",
                whatsapp_opted_in=True,
            )
            created = await user_repo.create(user)
            del _conversations[phone]
            return PROMPTS["success"].format(user_id=created.id), created.id

        elif text.lower() in ("no", "n", "nahi"):
            _conversations[phone] = {"step": "name", "data": {"phone": phone}}
            return PROMPTS["restart"], None

        else:
            return "Please type *yes* to confirm or *no* to start over.", None

    del _conversations[phone]
    return PROMPTS["welcome"], None


async def _send_reply(phone: str, text: str) -> None:
    """Send a WhatsApp text message back via OpenClaw API."""
    if not settings.openclaw_api_key or not settings.openclaw_phone_id:
        logger.info("WhatsApp reply (no OpenClaw config): %s -> %s", phone, text[:80])
        return

    import httpx

    url = f"https://graph.facebook.com/v18.0/{settings.openclaw_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.openclaw_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("WhatsApp reply sent to %s", phone)
    except Exception:
        logger.exception("Failed to send WhatsApp reply to %s", phone)
