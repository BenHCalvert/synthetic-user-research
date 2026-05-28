"""
IDL (Idaho Department of Lands) auction page monitor.
Uses requests + BeautifulSoup — no JS needed for this page.
"""

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import IDL_URL
from scrapers.parser import parse_price, parse_acreage

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux aarch64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
REQUEST_TIMEOUT = 30


def scrape_idl() -> list[dict]:
    """Synchronous scrape of the IDL real-estate-for-sale page."""
    try:
        resp = requests.get(IDL_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("IDL fetch failed: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = _parse_idl_page(soup)
    logger.info("IDL: found %d items", len(results))
    return results


def _parse_idl_page(soup: BeautifulSoup) -> list[dict]:
    items = []

    # IDL's real-estate page lists properties in various formats.
    # Common patterns: table rows, article elements, or div.property-listing

    # Pattern 1: table-based listing                                       # SELECTOR
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")[1:]  # skip header row
        for row in rows:
            item = _parse_table_row(row)
            if item:
                items.append(item)
        if items:
            return items

    # Pattern 2: article / card-based listing                             # SELECTOR
    cards = soup.find_all(["article", "div"], class_=re.compile(r"property|listing|parcel", re.I))
    for card in cards:
        item = _parse_card(card)
        if item:
            items.append(item)

    # Pattern 3: generic — scan all <a> tags with PDF or detail links
    if not items:
        items = _parse_links(soup)

    return items


def _parse_table_row(row) -> dict | None:
    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
        return None

    text = row.get_text(" ", strip=True)
    link = row.find("a")
    if not link:
        return None

    href = link.get("href", "")
    url = urljoin(IDL_URL, href) if href else IDL_URL
    title = link.get_text(strip=True) or cells[0].get_text(strip=True)

    return _build_item(url, title, text, row)


def _parse_card(card) -> dict | None:
    link = card.find("a")
    if not link:
        return None
    href = link.get("href", "")
    url = urljoin(IDL_URL, href) if href else IDL_URL
    title = link.get_text(strip=True) or card.get_text(" ", strip=True)[:80]
    text = card.get_text(" ", strip=True)
    return _build_item(url, title, text, card)


def _parse_links(soup: BeautifulSoup) -> list[dict]:
    items = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Look for links that look like property listings
        if any(kw in href.lower() for kw in ["parcel", "property", "sale", "auction", "land"]):
            url = urljoin(IDL_URL, href)
            text = a.get_text(strip=True)
            if len(text) > 5:
                items.append(_build_item(url, text, text, a))
    return items


def _build_item(url: str, title: str, text: str, element) -> dict:
    acreage = parse_acreage(text)
    price = parse_price(text)
    location = _extract_location(text, title)

    return {
        "url": url,
        "title": title[:255],
        "description": text[:2000],
        "location": location,
        "acreage": acreage,
        "asking_price": price,
        "status": "Active",
        "date_posted": _extract_date(text),
        "raw_snippet": text[:500],
    }


def _extract_location(text: str, title: str) -> str | None:
    # Try to extract county or city name
    m = re.search(r"(\w[\w\s]+County)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Look for Idaho city names from our target zones
    cities = ["salmon", "mackay", "stanley", "lowman", "garden valley", "challis", "lemhi", "custer"]
    text_lower = (text + " " + title).lower()
    for city in cities:
        if city in text_lower:
            return city.title()
    return None


def _extract_date(text: str) -> str | None:
    m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
                  text, re.IGNORECASE)
    return m.group(0) if m else None
