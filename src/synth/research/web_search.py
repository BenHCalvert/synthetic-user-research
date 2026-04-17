"""Web search wrapper supporting DuckDuckGo (free), Tavily, SerpAPI, and Brave."""

from __future__ import annotations

import httpx

from synth.models.config import AppConfig


class SearchResult:
    """A single search result."""

    def __init__(self, title: str, url: str, snippet: str, content: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.content = content


class WebSearcher:
    """Unified web search across providers."""

    def __init__(self, provider: str | None = None):
        if provider is None:
            config = AppConfig.load()
            provider = config.web_search.provider
        self.provider = provider

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Run a web search and return results."""
        if self.provider == "duckduckgo":
            return await self._duckduckgo_search(query, max_results)
        elif self.provider == "tavily":
            return await self._tavily_search(query, max_results)
        elif self.provider == "serpapi":
            return await self._serpapi_search(query, max_results)
        elif self.provider == "brave":
            return await self._brave_search(query, max_results)
        else:
            raise ValueError(f"Unknown search provider: {self.provider}")

    async def _duckduckgo_search(self, query: str, max_results: int) -> list[SearchResult]:
        """Search via DuckDuckGo (no API key required)."""
        import asyncio

        from duckduckgo_search import DDGS

        def _run() -> list[SearchResult]:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
                for r in results
            ]

        return await asyncio.get_event_loop().run_in_executor(None, _run)

    async def _tavily_search(self, query: str, max_results: int) -> list[SearchResult]:
        """Search via Tavily API."""
        import os

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY not set")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_raw_content": True,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                content=r.get("raw_content", ""),
            )
            for r in data.get("results", [])
        ]

    async def _serpapi_search(self, query: str, max_results: int) -> list[SearchResult]:
        """Search via SerpAPI."""
        import os

        api_key = os.environ.get("SERPAPI_API_KEY")
        if not api_key:
            raise RuntimeError("SERPAPI_API_KEY not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "api_key": api_key,
                    "q": query,
                    "num": max_results,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("snippet", ""),
            )
            for r in data.get("organic_results", [])
        ]

    async def _brave_search(self, query: str, max_results: int) -> list[SearchResult]:
        """Search via Brave Search API."""
        import os

        api_key = os.environ.get("BRAVE_API_KEY")
        if not api_key:
            raise RuntimeError("BRAVE_API_KEY not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": max_results},
                headers={"X-Subscription-Token": api_key},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("description", ""),
            )
            for r in data.get("web", {}).get("results", [])
        ]
