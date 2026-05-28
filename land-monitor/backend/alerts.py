"""Telegram alert sender. Sends a message for new listings and IDL auctions."""

import logging
from telegram import Bot
from telegram.error import TelegramError

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def _make_bot() -> Bot | None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured; skipping alert")
        return None
    return Bot(token=TELEGRAM_BOT_TOKEN)


def _score_emoji(score: float | None) -> str:
    if score is None:
        return "⬜"
    if score >= 75:
        return "🟢"
    if score >= 50:
        return "🟡"
    if score >= 25:
        return "🟠"
    return "🔴"


async def send_listing_alert(listing: dict) -> None:
    bot = _make_bot()
    if bot is None:
        return

    score = listing.get("score")
    emoji = _score_emoji(score)
    price = listing.get("price")
    price_str = f"${price:,}" if price else "N/A"
    acres = listing.get("acreage")
    acres_str = f"{acres:.1f} ac" if acres else "N/A"
    ppa = listing.get("price_per_acre")
    ppa_str = f"${ppa:,.0f}/ac" if ppa else "N/A"

    flags = []
    if listing.get("nf_adjacency") in ("inholding", "adjacent"):
        flags.append("🌲 NF Adjacent")
    if listing.get("in_snra"):
        flags.append("⚠️ SNRA")
    if listing.get("is_mining_claim"):
        flags.append("⛏️ Mining Claim")
    flag_str = "  ".join(flags)

    text = (
        f"{emoji} *New Listing — Score {score or 'N/A'}*\n"
        f"{listing.get('title', 'Untitled')}\n\n"
        f"💰 {price_str}  |  📐 {acres_str}  |  📊 {ppa_str}\n"
        f"📍 Zone: {listing.get('zone') or 'Unknown'}\n"
        f"🚗 Access: {listing.get('access_type') or 'Unknown'}\n"
        f"💧 Water: {listing.get('water') or 'Unknown'}\n"
        f"⚡ Utilities: {listing.get('utilities') or 'Unknown'}\n"
    )
    if flag_str:
        text += f"\n{flag_str}\n"
    text += f"\n🔗 {listing.get('url', '')}"

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except TelegramError as e:
        logger.error("Failed to send Telegram alert: %s", e)


async def send_idl_alert(auction: dict) -> None:
    bot = _make_bot()
    if bot is None:
        return

    price = auction.get("asking_price")
    price_str = f"${price:,}" if price else "Price TBD"

    text = (
        f"🏛️ *New IDL Auction Listing*\n"
        f"{auction.get('title', 'Untitled')}\n\n"
        f"📍 {auction.get('location') or 'Location unknown'}\n"
        f"💰 {price_str}\n"
        f"📐 {auction.get('acreage') or 'N/A'} acres\n"
        f"📅 Posted: {auction.get('date_posted') or 'Unknown'}\n"
        f"\n🔗 {auction.get('url', '')}"
    )

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except TelegramError as e:
        logger.error("Failed to send IDL Telegram alert: %s", e)
