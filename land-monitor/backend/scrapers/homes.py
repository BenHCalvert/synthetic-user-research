"""
Homes.com scraper using Playwright (async, headless Chromium).

Homes.com renders search results via React/JavaScript, so Playwright is required.
Update SELECTOR-marked lines if the site changes its DOM structure.
"""

import asyncio
import logging
from urllib.parse import urljoin

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from config import HOMES_URLS, BROWSER_TIMEOUT_MS, PAGE_LOAD_TIMEOUT_MS, SCRAPE_DELAY_SECONDS
from scrapers.parser import extract_keywords, classify_zone, parse_price, parse_acreage

logger = logging.getLogger(__name__)

BASE_URL = "https://www.homes.com"


async def scrape_homes() -> list[dict]:
    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        context.set_default_timeout(BROWSER_TIMEOUT_MS)

        for url in HOMES_URLS:
            try:
                page_results = await _scrape_search_page(context, url)
                results.extend(page_results)
                await asyncio.sleep(SCRAPE_DELAY_SECONDS)
            except Exception as e:
                logger.error("Homes.com error scraping %s: %s", url, e)

        await browser.close()

    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)
    logger.info("Homes.com: scraped %d unique listings", len(deduped))
    return deduped


async def _scrape_search_page(context, search_url: str) -> list[dict]:
    page = await context.new_page()
    results = []

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)

        # Homes.com may show a cookie/consent banner — dismiss it          # SELECTOR
        try:
            accept_btn = await page.query_selector("button[id*='accept'], button[class*='accept-cookies']")
            if accept_btn:
                await accept_btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Wait for listing cards                                           # SELECTOR
        try:
            await page.wait_for_selector(
                ".listing-card, [data-testid='listing-card'], .property-card, article[class*='listing']",
                timeout=20_000,
            )
        except PlaywrightTimeout:
            logger.warning("No listings found at %s", search_url)
            return []

        # Scroll to load lazy-loaded content
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)

        cards = await page.query_selector_all(
            ".listing-card, [data-testid='listing-card'], .property-card, article[class*='listing']"  # SELECTOR
        )

        for card in cards:
            try:
                listing = await _parse_card(card)
                if listing:
                    results.append(listing)
            except Exception as e:
                logger.debug("Homes.com card parse error: %s", e)

    finally:
        await page.close()

    return results


async def _parse_card(card) -> dict | None:
    # --- URL ---                                                          # SELECTOR
    link_el = await card.query_selector("a[href]")
    if not link_el:
        return None
    href = await link_el.get_attribute("href")
    if not href:
        return None
    url = urljoin(BASE_URL, href) if href.startswith("/") else href

    # --- Title ---                                                        # SELECTOR
    title_el = await card.query_selector("h2, h3, .listing-title, [data-testid='address'], .property-address")
    title = (await title_el.inner_text()).strip() if title_el else None

    card_text = await card.inner_text()

    # --- Price ---                                                        # SELECTOR
    price_el = await card.query_selector(".price, [data-testid='price'], .listing-price, .card-price")
    price_text = (await price_el.inner_text()).strip() if price_el else ""
    price = parse_price(price_text) or parse_price(card_text)

    # --- Acreage ---
    acreage = parse_acreage(card_text)

    # --- Thumbnail ---                                                    # SELECTOR
    img_el = await card.query_selector("img")
    thumbnail_url = None
    if img_el:
        thumbnail_url = (await img_el.get_attribute("src") or
                         await img_el.get_attribute("data-src") or
                         await img_el.get_attribute("data-lazy"))
        if thumbnail_url and thumbnail_url.startswith("data:"):
            thumbnail_url = None

    # --- Address ---                                                      # SELECTOR
    addr_el = await card.query_selector(".address, [data-testid='address'], .listing-address, .property-address")
    address = (await addr_el.inner_text()).strip() if addr_el else title

    price_per_acre = round(price / acreage, 2) if price and acreage and acreage > 0 else None

    text_blob = f"{title or ''} {address or ''} {card_text}"
    kw = extract_keywords(text_blob)
    zone = classify_zone(address or "", title or "")

    return {
        "url": url,
        "source": "Homes",
        "title": title,
        "address": address,
        "zone": zone,
        "price": price,
        "acreage": acreage,
        "price_per_acre": price_per_acre,
        "thumbnail_url": thumbnail_url,
        "agent_name": None,
        "status": "Active",
        **kw,
    }
