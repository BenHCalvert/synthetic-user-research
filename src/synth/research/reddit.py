"""Reddit search and content fetching."""

from __future__ import annotations

import httpx
from rich.console import Console

console = Console()


class RedditResult:
    """A Reddit post or comment."""

    def __init__(
        self,
        title: str,
        url: str,
        selftext: str,
        score: int,
        subreddit: str,
        num_comments: int,
    ):
        self.title = title
        self.url = url
        self.selftext = selftext
        self.score = score
        self.subreddit = subreddit
        self.num_comments = num_comments


async def search_reddit(
    query: str,
    subreddits: list[str] | None = None,
    max_results: int = 10,
    sort: str = "relevance",
) -> list[RedditResult]:
    """Search Reddit for posts matching a query."""
    results: list[RedditResult] = []

    async with httpx.AsyncClient() as client:
        if subreddits:
            for sub in subreddits:
                url = f"https://www.reddit.com/r/{sub}/search.json"
                params = {
                    "q": query,
                    "restrict_sr": "on",
                    "sort": sort,
                    "limit": max_results,
                    "t": "year",
                }
                try:
                    response = await client.get(
                        url,
                        params=params,
                        headers={"User-Agent": "synth-research/0.1"},
                        timeout=15.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    results.extend(_parse_reddit_response(data))
                except Exception as e:
                    console.print(f"[yellow]Reddit search failed for r/{sub}: {e}[/yellow]")
        else:
            url = "https://www.reddit.com/search.json"
            params = {"q": query, "sort": sort, "limit": max_results, "t": "year"}
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers={"User-Agent": "synth-research/0.1"},
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()
                results.extend(_parse_reddit_response(data))
            except Exception as e:
                console.print(f"[yellow]Reddit search failed: {e}[/yellow]")

    # Sort by engagement
    results.sort(key=lambda r: r.score + r.num_comments, reverse=True)
    return results[:max_results]


def _parse_reddit_response(data: dict) -> list[RedditResult]:  # type: ignore[type-arg]
    """Parse Reddit JSON API response into RedditResult objects."""
    results: list[RedditResult] = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        results.append(
            RedditResult(
                title=post.get("title", ""),
                url=f"https://reddit.com{post.get('permalink', '')}",
                selftext=post.get("selftext", "")[:1000],
                score=post.get("score", 0),
                subreddit=post.get("subreddit", ""),
                num_comments=post.get("num_comments", 0),
            )
        )
    return results
