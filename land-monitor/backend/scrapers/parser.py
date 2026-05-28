"""
Shared parsing utilities: price/acreage extraction, keyword analysis, zone classification.
"""

import re
from config import KEYWORDS, ZONES


def parse_price(text: str) -> int | None:
    if not text:
        return None
    text = text.replace(",", "").replace(" ", "")
    m = re.search(r"\$?([\d]+(?:\.\d+)?)[kKmM]?", text)
    if not m:
        return None
    val = float(m.group(1))
    suffix = text[m.end():m.end() + 1].lower()
    if suffix == "k":
        val *= 1_000
    elif suffix == "m":
        val *= 1_000_000
    return int(val) if val > 0 else None


def parse_acreage(text: str) -> float | None:
    if not text:
        return None
    # Match patterns like "12.5 Acres", "5 ac", "0.75 acre"
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:acres?|ac\b)", text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_keywords(text: str) -> dict:
    """
    Run all keyword patterns against text. Returns a dict with keys:
    nf_adjacency, access_type, water, utilities, is_mining_claim, in_snra
    """
    text_lower = text.lower()
    result = {}

    result["nf_adjacency"] = _match_first(text_lower, KEYWORDS["nf_adjacency"])
    result["access_type"] = _match_first(text_lower, KEYWORDS["access_type"])
    result["water"] = _match_first(text_lower, KEYWORDS["water"])
    result["utilities"] = _match_first(text_lower, KEYWORDS["utilities"])

    result["is_mining_claim"] = any(kw in text_lower for kw in KEYWORDS["is_mining_claim"])
    result["in_snra"] = any(kw in text_lower for kw in KEYWORDS["in_snra"])

    return result


def _match_first(text_lower: str, pattern_dict: dict) -> str | None:
    for category, patterns in pattern_dict.items():
        if category == "unknown":
            continue
        if any(p in text_lower for p in patterns):
            return category
    return "unknown"


def classify_zone(address: str, title: str = "", description: str = "") -> str | None:
    text = f"{address} {title} {description}".lower()
    best_zone = None
    best_priority = 99

    for zone_name, zone_data in ZONES.items():
        # Check county mentions
        county_match = any(c.lower() in text for c in zone_data["counties"])
        # Check keyword mentions
        kw_match = any(kw in text for kw in zone_data["keywords"])

        if kw_match:
            # Keyword match takes precedence and narrows county down
            if zone_data["priority"] < best_priority:
                best_zone = zone_name
                best_priority = zone_data["priority"]
        elif county_match and best_zone is None:
            best_zone = zone_name
            best_priority = zone_data["priority"]

    return best_zone
