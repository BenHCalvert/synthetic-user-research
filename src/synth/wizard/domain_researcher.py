"""Auto-research a product domain to generate initial context."""

from __future__ import annotations

from rich.console import Console

from synth.core.llm import LLM
from synth.models.config import AppConfig
from synth.models.persona import DomainContext
from synth.research.web_search import WebSearcher

console = Console()


async def research_domain(domain: str, product_name: str = "") -> DomainContext:
    """Research a product domain and generate initial context."""
    config = AppConfig.load()
    llm = LLM(config.models)
    model_label = llm.available_labels[0]

    # Search for domain info
    searcher = WebSearcher()
    queries = [
        f"{product_name or domain} user reviews",
        f"{product_name or domain} common complaints",
        f"{domain} user roles personas",
    ]

    findings = []
    for query in queries:
        try:
            results = await searcher.search(query, max_results=5)
            for r in results:
                findings.append(f"- {r.title}: {r.snippet}")
        except Exception:
            pass

    # Synthesize into domain context
    system = (
        "Based on web research, identify the main user roles, frustrations, "
        "and segments for this product domain. Return structured data."
    )
    messages = [
        {
            "role": "user",
            "content": (
                f"Domain: {domain}\nProduct: {product_name}\n\n"
                f"Research findings:\n" + "\n".join(findings)
            ),
        }
    ]

    result = await llm.structured_complete(system, messages, model_label, DomainContext)
    return result  # type: ignore[return-value]
