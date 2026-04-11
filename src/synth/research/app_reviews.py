"""App store review fetcher for Apple App Store and Google Play."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

if TYPE_CHECKING:
    from datetime import date

console = Console()


def _safe_int(value: str | int, default: int = 3) -> int:
    """Safely parse an integer, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class AppReview:
    """A single app store review."""

    def __init__(
        self,
        text: str,
        rating: int,
        date: str,
        store: str,
        title: str = "",
    ):
        self.text = text
        self.rating = rating
        self.date = date
        self.store = store
        self.title = title


async def fetch_app_reviews(
    app_id: str,
    store: str = "apple",
    max_results: int = 50,
    recency_cutoff: date | None = None,
) -> list[AppReview]:
    """Fetch reviews from an app store.

    Note: This uses public RSS/API endpoints. For production use,
    consider a dedicated scraping service.
    """
    if store == "apple":
        return await _fetch_apple_reviews(app_id, max_results)
    elif store == "google":
        return await _fetch_google_reviews(app_id, max_results)
    else:
        console.print(f"[yellow]Unknown store: {store}[/yellow]")
        return []


async def _fetch_apple_reviews(app_id: str, max_results: int) -> list[AppReview]:
    """Fetch Apple App Store reviews via the iTunes RSS feed."""
    reviews: list[AppReview] = []

    async with httpx.AsyncClient() as client:
        # Apple provides an RSS feed for reviews
        url = f"https://itunes.apple.com/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
        try:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            data = response.json()

            entries = data.get("feed", {}).get("entry", [])
            for entry in entries[:max_results]:
                if isinstance(entry.get("content"), dict):
                    reviews.append(
                        AppReview(
                            text=entry.get("content", {}).get("label", ""),
                            rating=_safe_int(entry.get("im:rating", {}).get("label", "3")),
                            date=entry.get("updated", {}).get("label", ""),
                            store="apple",
                            title=entry.get("title", {}).get("label", ""),
                        )
                    )
        except httpx.HTTPError as e:
            console.print(f"[yellow]Apple review fetch failed: {e}[/yellow]")

    return reviews


async def _fetch_google_reviews(app_id: str, max_results: int) -> list[AppReview]:
    """Fetch Google Play reviews by scraping the web page.

    Note: This is fragile and may break. For production, use a dedicated API.
    """
    reviews: list[AppReview] = []

    async with httpx.AsyncClient() as client:
        url = f"https://play.google.com/store/apps/details?id={app_id}&hl=en&gl=us"
        try:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; synth-research/0.1)"},
                timeout=15.0,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            review_elements = soup.select("[jscontroller] div[class*='review']")

            for elem in review_elements[:max_results]:
                text = elem.get_text(strip=True)
                if text:
                    reviews.append(
                        AppReview(
                            text=text[:500],
                            rating=3,  # Difficult to extract reliably
                            date="",
                            store="google",
                        )
                    )
        except httpx.HTTPError as e:
            console.print(f"[yellow]Google Play review fetch failed: {e}[/yellow]")

    return reviews
