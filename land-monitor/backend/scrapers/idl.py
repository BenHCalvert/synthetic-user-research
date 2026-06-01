"""
IDL (Idaho Department of Lands) auction page monitor.
Uses requests + BeautifulSoup — no JS needed for this page.
"""

import logging
import re
from urllib.parse import urljoin, urlparse

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
IDL_HOST = "idl.idaho.gov"

# Link text that signals navigation/social chrome, not a property listing
JUNK_TITLE_RE = re.compile(
    r"^(facebook|twitter|instagram|youtube|linkedin|x\.com|icon|logo|"
    r"menu|home|back|next|previous|search|share|print|email|rss|"
    r"sell your land|contact|about|subscribe|sign.?up|skip to)$",
    re.I,
)

# URL path fragments that indicate non-listing pages
EXCLUDED_PATH_RE = re.compile(
    r"/(sell-land|contact|about|news|events|jobs|careers|login|"
    r"sitemap|privacy|terms|social|donate|subscribe|sign-up|"
    r"facebook|twitter|instagram|youtube)/",
    re.I,
)

EXTERNAL_DOMAINS = {
    "facebook.com", "twitter.com", "instagram.com", "youtube.com",
    "linkedin.com", "x.com", "tiktok.com", "pinterest.com",
}

IDAHO_COUNTIES = [
    "boise", "elmore", "custer", "lemhi", "blaine", "valley", "adams",
    "idaho", "clearwater", "shoshone", "benewah", "boundary",
]

IDAHO_CITIES = [
    "salmon", "mackay", "stanley", "lowman", "garden valley", "challis",
    "lemhi", "gibbonsville", "cobalt", "north fork", "leadore", "arco",
    "moore", "clayton", "sunbeam", "redfish", "atlanta", "pine",
    "featherville", "crouch", "banks", "horseshoe bend",
]


def scrape_idl() -> list[dict]:
    """Synchronous scrape of the IDL real-estate-for-sale page."""
    try:
        resp = requests.get(IDL_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("IDL fetch failed: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    # Strip page chrome before parsing so we don't pick up nav/footer links
    for tag in soup.find_all(["header", "footer", "nav",
                               "aside", ".sidebar", ".social-links"]):
        tag.decompose()

    results = _parse_idl_page(soup)
    valid = [r for r in results if _is_valid_listing(r)]
    logger.info("IDL: found %d valid items (filtered from %d raw)", len(valid), len(results))
    return valid


def _parse_idl_page(soup: BeautifulSoup) -> list[dict]:
    # Focus on main content area if present                                # SELECTOR
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"main|content|primary", re.I))
        or soup.find(class_=re.compile(r"entry-content|page-content|main-content", re.I))
        or soup
    )

    items = []

    # Pattern 1: table rows
    table = main.find("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            item = _parse_table_row(row)
            if item:
                items.append(item)
        if items:
            return items

    # Pattern 2: article / card elements                                   # SELECTOR
    cards = main.find_all(
        ["article", "div"],
        class_=re.compile(r"property|listing|parcel|sale|auction|post", re.I),
    )
    for card in cards:
        item = _parse_card(card)
        if item:
            items.append(item)

    if items:
        return items

    # Pattern 3: WordPress post entries (IDL site is WordPress)
    posts = main.find_all(class_=re.compile(r"wp-block|entry|post-\d+", re.I))
    for post in posts:
        item = _parse_card(post)
        if item:
            items.append(item)

    if items:
        return items

    # Pattern 4: Targeted link scan — IDL-domain links only, no chrome
    return _parse_links(main)


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
    return _build_item(url, title, text)


def _parse_card(card) -> dict | None:
    link = card.find("a")
    if not link:
        return None
    href = link.get("href", "")
    if not href or _is_junk_href(href):
        return None
    url = urljoin(IDL_URL, href)
    title = link.get_text(strip=True) or card.get_text(" ", strip=True)[:80]
    if JUNK_TITLE_RE.match(title):
        return None
    text = card.get_text(" ", strip=True)
    return _build_item(url, title, text)


def _parse_links(content) -> list[dict]:
    """Last-resort: only collect links that point to IDL's own domain and
    look like property pages (PDF listing sheets or detail pages)."""
    items = []
    seen_urls = set()

    for a in content.find_all("a", href=True):
        href = a["href"]
        if _is_junk_href(href):
            continue

        # Resolve URL and check it stays on IDL's domain
        url = urljoin(IDL_URL, href)
        parsed = urlparse(url)
        if parsed.netloc and IDL_HOST not in parsed.netloc:
            continue

        # Require the link itself (or its parent paragraph) to mention
        # land-related content — acres, county, price, parcel, etc.
        parent_text = ""
        parent = a.parent
        if parent:
            parent_text = parent.get_text(" ", strip=True)

        combined = f"{a.get_text(strip=True)} {parent_text}".lower()
        has_land_signal = any(w in combined for w in [
            "acre", "county", "parcel", "section", "township",
            "range", "mineral", "timber", "auction", "bid",
        ])
        if not has_land_signal:
            continue

        title = a.get_text(strip=True)
        if not title or JUNK_TITLE_RE.match(title) or len(title) < 6:
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        items.append(_build_item(url, title, parent_text or title))

    return items


def _build_item(url: str, title: str, text: str) -> dict:
    return {
        "url": url,
        "title": title[:255],
        "description": text[:2000],
        "location": _extract_location(text, title),
        "acreage": parse_acreage(text) or parse_acreage(title),
        "asking_price": parse_price(text),
        "status": "Active",
        "date_posted": _extract_date(text),
        "raw_snippet": text[:500],
    }


def _is_valid_listing(item: dict) -> bool:
    """Reject entries that are clearly page chrome rather than real listings."""
    title = item.get("title", "")

    # Must not be a junk title
    if JUNK_TITLE_RE.match(title):
        return False

    # Must not point to social media or excluded paths
    url = item.get("url", "")
    if _is_junk_href(url):
        return False

    # Must have at least one real data signal
    has_signal = (
        item.get("acreage") is not None
        or item.get("asking_price") is not None
        or item.get("location") is not None
        or _has_idaho_reference(title + " " + item.get("description", ""))
    )
    return has_signal


def _has_idaho_reference(text: str) -> bool:
    text_lower = text.lower()
    return (
        any(c in text_lower for c in IDAHO_COUNTIES)
        or any(c in text_lower for c in IDAHO_CITIES)
        or "idaho" in text_lower
        or re.search(r"\bacre[s]?\b", text_lower) is not None
    )


def _is_junk_href(href: str) -> bool:
    parsed = urlparse(href)
    domain = parsed.netloc.lower().lstrip("www.")
    if any(d in domain for d in EXTERNAL_DOMAINS):
        return True
    if EXCLUDED_PATH_RE.search(href):
        return True
    return False


def _extract_location(text: str, title: str) -> str | None:
    combined = f"{text} {title}"
    m = re.search(r"(\w[\w\s]+County)", combined, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    text_lower = combined.lower()
    for city in IDAHO_CITIES:
        if city in text_lower:
            return city.title()
    for county in IDAHO_COUNTIES:
        if county in text_lower:
            return f"{county.title()} County"
    return None


def _extract_date(text: str) -> str | None:
    m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if m:
        return m.group(1)
    m = re.search(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        text, re.IGNORECASE,
    )
    return m.group(0) if m else None
