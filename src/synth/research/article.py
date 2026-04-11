"""Article content extractor using httpx + BeautifulSoup."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()


class ArticleContent:
    """Extracted article content."""

    def __init__(self, title: str, url: str, text: str, word_count: int):
        self.title = title
        self.url = url
        self.text = text
        self.word_count = word_count


async def extract_article(url: str) -> ArticleContent | None:
    """Fetch and extract main content from a web article."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; synth-research/0.1)"},
                timeout=15.0,
                follow_redirects=True,
            )
            response.raise_for_status()
        except Exception as e:
            console.print(f"[yellow]Failed to fetch {url}: {e}[/yellow]")
            return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Remove script, style, nav, footer elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try to find main content area
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        return None

    # Extract text from paragraphs
    paragraphs = main.find_all("p")
    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    if not text:
        return None

    # Truncate to reasonable length
    words = text.split()
    if len(words) > 2000:
        text = " ".join(words[:2000]) + "..."

    return ArticleContent(
        title=title,
        url=url,
        text=text,
        word_count=len(words),
    )


async def extract_articles(urls: list[str]) -> list[ArticleContent]:
    """Extract content from multiple articles."""
    results: list[ArticleContent] = []
    for url in urls:
        article = await extract_article(url)
        if article:
            results.append(article)
    return results
