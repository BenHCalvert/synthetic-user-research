"""
Scores a listing 0–100 based on how well it matches the target criteria.
Higher is better. Call score_listing() after parsing; result stored in DB.
"""

from config import ZONES, SCORE_WEIGHTS


def score_listing(listing: dict) -> float:
    total = 0.0

    total += _score_nf_adjacency(listing.get("nf_adjacency")) * (SCORE_WEIGHTS["nf_adjacency"] / 100)
    total += _score_price_per_acre(listing.get("price_per_acre")) * (SCORE_WEIGHTS["price_per_acre"] / 100)
    total += _score_access(listing.get("access_type")) * (SCORE_WEIGHTS["access"] / 100)
    total += _score_water(listing.get("water")) * (SCORE_WEIGHTS["water"] / 100)
    total += _score_acreage(listing.get("acreage")) * (SCORE_WEIGHTS["acreage"] / 100)
    total += _score_zone(listing.get("zone")) * (SCORE_WEIGHTS["zone_priority"] / 100)
    total += _score_utilities(listing.get("utilities")) * (SCORE_WEIGHTS["utilities"] / 100)

    # Apply penalties
    if listing.get("in_snra"):
        total *= 0.85  # SNRA restrictions reduce appeal
    if listing.get("is_mining_claim"):
        total *= 0.95  # mining claims have title complexity

    return round(min(max(total, 0.0), 100.0), 1)


# --- Individual dimension scorers (each returns 0–100 before weighting) ---

def _score_nf_adjacency(value: str | None) -> float:
    return {
        "inholding": 100,
        "adjacent": 85,
        "near": 50,
        "none": 10,
        None: 20,
    }.get(value, 20)


def _score_price_per_acre(ppa: float | None) -> float:
    if ppa is None:
        return 40
    if ppa < 3_000:
        return 100
    if ppa < 6_000:
        return 85
    if ppa < 10_000:
        return 65
    if ppa < 18_000:
        return 40
    if ppa < 30_000:
        return 20
    return 5


def _score_access(value: str | None) -> float:
    return {
        "year_round_paved": 100,
        "year_round_gravel": 85,
        "seasonal": 45,
        "hike_in": 15,
        "unknown": 35,
        None: 35,
    }.get(value, 35)


def _score_water(value: str | None) -> float:
    return {
        "drilled_well": 100,
        "creek_river": 85,
        "community": 65,
        "none": 5,
        "unknown": 40,
        None: 40,
    }.get(value, 40)


def _score_acreage(acres: float | None) -> float:
    if acres is None:
        return 50
    if 5 <= acres <= 15:
        return 100
    if 3 <= acres < 5 or 15 < acres <= 20:
        return 80
    if 1 <= acres < 3 or 20 < acres <= 35:
        return 55
    if acres < 1:
        return 30
    return 20  # > 35 acres is over budget range anyway


def _score_zone(zone: str | None) -> float:
    if zone is None:
        return 20
    zone_data = ZONES.get(zone, {})
    priority = zone_data.get("priority", 3)
    return {1: 100, 2: 65, 3: 30}.get(priority, 20)


def _score_utilities(value: str | None) -> float:
    return {
        "power": 100,
        "off_grid": 60,
        "unknown": 40,
        None: 40,
    }.get(value, 40)
