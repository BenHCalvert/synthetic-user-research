"""
LandWatch scraper using Playwright (async, headless Chromium).

Selectors are based on LandWatch's typical DOM structure as of 2024.
If the site redesigns, update the CSS selectors marked with # SELECTOR.
"""

import asyncio
import logging
import re
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

from config import LANDWATCH_URLS, BROWSER_TIMEOUT_MS, PAGE_LOAD_TIMEOUT_MS, SCRAPE_DELAY_SECONDS
from scrapers.parser import extract_keywords, classify_zone, parse_price, parse_acreage

logger = logging.getLogger(__name__)

BASE_URL = "https://www.landwatch.com"


async def scrape_landwatch() -> list[dict]:
    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        context.set_default_timeout(BROWSER_TIMEOUT_MS)

        for url in LANDWATCH_URLS:
            try:
                page_results = await _scrape_search_page(context, url)
                results.extend(page_results)
                await asyncio.sleep(SCRAPE_DELAY_SECONDS)
            except Exception as e:
                logger.error("LandWatch error scraping %s: %s", url, e)

        await browser.close()

    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)
    logger.info("LandWatch: scraped %d unique listings", len(deduped))
    return deduped


async def _scrape_search_page(context, search_url: str) -> list[dict]:
    page = await context.new_page()
    results = []
    current_url = search_url

    try:
        while current_url:
            await page.goto(current_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)

            # Wait for listing cards to appear                              # SELECTOR
            try:
                await page.wait_for_selector("article.property-card, [data-testid='property-card'], .listing-card",
                                             timeout=15_000)
            except PlaywrightTimeout:
                logger.warning("No listing cards found at %s", current_url)
                break

            cards = await page.query_selector_all(
                "article.property-card, [data-testid='property-card'], .listing-card"  # SELECTOR
            )
            if not cards:
                break

            for card in cards:
                try:
                    listing = await _parse_card(page, card)
                    if listing:
                        results.append(listing)
                except Exception as e:
                    logger.debug("Card parse error: %s", e)

            # Pagination — look for "Next" button                          # SELECTOR
            next_btn = await page.query_selector("a[aria-label='Next page'], a.pagination-next, [data-testid='next-page']")
            if next_btn:
                next_href = await next_btn.get_attribute("href")
                current_url = urljoin(BASE_URL, next_href) if next_href else None
                await asyncio.sleep(SCRAPE_DELAY_SECONDS)
            else:
                break
    finally:
        await page.close()

    return results


async def _parse_card(page: Page, card) -> dict | None:
    # --- URL (dedupe key) ---                                              # SELECTOR
    link_el = await card.query_selector("a[href*='/land/'], a[href*='/property/'], a.property-link, h2 a, h3 a")
    if not link_el:
        return None
    href = await link_el.get_attribute("href")
    if not href:
        return None
    url = urljoin(BASE_URL, href)

    # --- Title ---                                                        # SELECTOR
    title_el = await card.query_selector("h2, h3, .property-title, [data-testid='listing-title']")
    title = (await title_el.inner_text()).strip() if title_el else None

    # --- Price ---                                                        # SELECTOR
    price_el = await card.query_selector(".price, [data-testid='price'], .listing-price, .property-price")
    price_text = (await price_el.inner_text()).strip() if price_el else ""
    price = parse_price(price_text)

    # --- Acreage ---                                                      # SELECTOR
    # LandWatch typically shows "X Acres" or "X ac" in a details section
    card_text = await card.inner_text()
    acreage = parse_acreage(card_text)

    # --- Thumbnail ---                                                    # SELECTOR
    img_el = await card.query_selector("img")
    thumbnail_url = await img_el.get_attribute("src") if img_el else None
    if thumbnail_url and thumbnail_url.startswith("data:"):
        thumbnail_url = await img_el.get_attribute("data-src") or None

    # --- Address / location ---                                           # SELECTOR
    addr_el = await card.query_selector(".address, .location, [data-testid='address'], .property-location")
    address = (await addr_el.inner_text()).strip() if addr_el else _extract_location_from_title(title or "")

    # --- Agent ---                                                        # SELECTOR
    agent_el = await card.query_selector(".agent-name, .broker-name, [data-testid='agent-name']")
    agent_name = (await agent_el.inner_text()).strip() if agent_el else None

    # --- Status ---                                                       # SELECTOR
    status_el = await card.query_selector(".status-badge, .listing-status, [data-testid='status']")
    status_text = (await status_el.inner_text()).strip() if status_el else "Active"
    status = _parse_status(status_text)

    price_per_acre = round(price / acreage, 2) if price and acreage and acreage > 0 else None

    # Keyword extraction on what we have so far (full description fetched separately for new listings)
    text_blob = f"{title or ''} {address or ''} {card_text}"
    kw = extract_keywords(text_blob)
    zone = classify_zone(address or "", title or "")

    return {
        "url": url,
        "source": "LandWatch",
        "title": title,
        "address": address,
        "zone": zone,
        "price": price,
        "acreage": acreage,
        "price_per_acre": price_per_acre,
        "thumbnail_url": thumbnail_url,
        "agent_name": agent_name,
        "status": status,
        **kw,
    }


async def fetch_listing_description(url: str) -> str | None:
    """Fetch the full description text from an individual listing page."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)
            # SELECTOR: update if LandWatch changes their detail page structure
            desc_el = await page.query_selector(
                ".listing-description, [data-testid='description'], .property-description, .description-text"
            )
            if desc_el:
                return (await desc_el.inner_text()).strip()
            # Fallback: grab main content area text
            main_el = await page.query_selector("main, article, #listing-detail")
            return (await main_el.inner_text()).strip() if main_el else None
        except Exception as e:
            logger.debug("Could not fetch description for %s: %s", url, e)
            return None
        finally:
            await browser.close()


def _parse_status(text: str) -> str:
    text_lower = text.lower()
    if "contract" in text_lower or "pending" in text_lower:
        return "Under Contract"
    if "sold" in text_lower:
        return "Sold"
    return "Active"


def _extract_location_from_title(title: str) -> str:
    # Many listings encode location in the title, e.g. "20 Acres in Custer County, Idaho"
    m = re.search(r"in (.+?)(?:,|$)", title, re.IGNORECASE)
    return m.group(1).strip() if m else ""
