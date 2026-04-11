"""Research pipeline: orchestrates web search, Reddit, app reviews, article extraction."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from synth.core.llm import LLM
from synth.models.config import AppConfig
from synth.models.persona import ChangelogEntry, PersonaModel, RefreshSource
from synth.research.app_reviews import fetch_app_reviews
from synth.research.reddit import search_reddit
from synth.research.web_search import WebSearcher

if TYPE_CHECKING:
    from synth.core.persona_store import PersonaStore

console = Console()


async def _generate_search_queries(persona: PersonaModel, llm: LLM, model_label: str) -> list[str]:
    """Use LLM to generate targeted search queries from persona context."""
    system = (
        "Generate 5-8 web search queries to find real-world evidence about this user persona. "
        "Focus on pain points, workarounds, community discussions, and product complaints. "
        "Return one query per line, no numbering or bullets."
    )
    pain_points = "\n".join(f"- {pp.pain_point}" for pp in persona.workflows.pain_points)
    workarounds = "\n".join(f"- {w}" for w in persona.workflows.compensating_behaviors)

    messages = [
        {
            "role": "user",
            "content": (
                f"Persona: {persona.persona} ({persona.role})\n"
                f"Pain points:\n{pain_points}\n"
                f"Workarounds:\n{workarounds}"
            ),
        }
    ]

    response = await llm.complete(system, messages, model_label)
    return [q.strip() for q in response.strip().split("\n") if q.strip()]


async def run_research_pipeline(persona: PersonaModel, store: PersonaStore, slug: str) -> None:
    """Run the full research pipeline for a persona."""
    config = AppConfig.load()
    llm = LLM(config.models)
    model_label = llm.available_labels[0]

    console.print(
        Panel(
            f"[bold]Researching: {persona.persona}[/bold]\nRole: {persona.role}",
            title="synth persona research",
        )
    )

    # Generate search queries
    console.print("[dim]Generating search queries...[/dim]")
    queries = await _generate_search_queries(persona, llm, model_label)
    console.print(f"Generated {len(queries)} queries.")

    # Web search
    console.print("[dim]Running web search...[/dim]")
    searcher = WebSearcher()
    all_search_results = []
    for query in queries:
        try:
            results = await searcher.search(query, max_results=5)
            all_search_results.extend(results)
            console.print(f"  [green]✓[/green] {query}: {len(results)} results")
        except Exception as e:
            console.print(f"  [yellow]✗[/yellow] {query}: {e}")

    # Reddit search
    console.print("[dim]Searching Reddit...[/dim]")
    domain_ctx = store.load_domain_context()
    subreddits = None
    if domain_ctx and "subreddits" in domain_ctx.research_sources:
        subs = domain_ctx.research_sources["subreddits"]
        if isinstance(subs, list):
            subreddits = [s.replace("r/", "") for s in subs]

    reddit_results = []
    for query in queries[:3]:  # Limit Reddit queries
        try:
            results = await search_reddit(query, subreddits=subreddits, max_results=5)
            reddit_results.extend(results)
        except Exception as e:
            console.print(f"  [yellow]Reddit search failed: {e}[/yellow]")

    console.print(f"Found {len(reddit_results)} Reddit posts.")

    # App reviews (if configured)
    app_reviews = []
    if domain_ctx and "app_store_id" in domain_ctx.research_sources:
        app_id = domain_ctx.research_sources["app_store_id"]
        if isinstance(app_id, str):
            console.print("[dim]Fetching app reviews...[/dim]")
            app_reviews = await fetch_app_reviews(app_id)
            console.print(f"Found {len(app_reviews)} app reviews.")

    # Synthesize findings with LLM
    console.print("[dim]Synthesizing findings...[/dim]")

    web_text = "\n".join(f"- [{r.title}]({r.url}): {r.snippet}" for r in all_search_results[:20])
    reddit_text = "\n".join(
        f"- [r/{r.subreddit}] {r.title} (score: {r.score}): {r.selftext[:200]}"
        for r in reddit_results[:10]
    )
    review_text = "\n".join(f"- [{r.rating}/5] {r.text[:200]}" for r in app_reviews[:15])

    synthesis_prompt = (
        "You are updating a user persona with new research findings. "
        "Analyze the research and identify:\n"
        "1. New pain points not in the current persona\n"
        "2. Concrete examples and quotes with source citations\n"
        "3. Workarounds and compensating behaviors\n"
        "4. Known gaps the research couldn't fill\n\n"
        "Return a summary of changes to make."
    )
    messages = [
        {
            "role": "user",
            "content": (
                f"Current persona: {persona.persona} ({persona.role})\n\n"
                f"Web search findings:\n{web_text}\n\n"
                f"Reddit findings:\n{reddit_text}\n\n"
                f"App review findings:\n{review_text}"
            ),
        }
    ]

    synthesis = await llm.complete(synthesis_prompt, messages, model_label)

    # Present findings to user
    console.print(Panel(synthesis, title="Research Findings"))

    if Confirm.ask("Apply these findings to the persona?", default=True):
        # Update evidence section
        new_sources = [r.url for r in all_search_results[:10]]
        persona.evidence.web_sources.extend(new_sources)
        persona.evidence.key_findings.append(synthesis[:500])

        if app_reviews:
            persona.evidence.app_reviews_analyzed = (
                f"{len(app_reviews)} reviews fetched on {date.today()}"
            )
            persona.evidence.key_complaints.extend(
                [r.text[:100] for r in app_reviews[:5] if r.rating <= 3]
            )

        # Update metadata
        persona.last_refreshed = date.today()
        persona.version = round(persona.version + 0.1, 1)
        persona.refresh_sources.append(
            RefreshSource(source="Web research pipeline", date=date.today())
        )
        persona.changelog.append(
            ChangelogEntry(date=date.today(), change="Enriched via web research pipeline")
        )

        store.save(persona, slug)
        console.print(f"[green]Persona '{slug}' updated (v{persona.version}).[/green]")
    else:
        console.print("[yellow]Changes discarded.[/yellow]")


async def run_refresh_pipeline(slugs: list[str], store: PersonaStore) -> None:
    """Re-research and update existing personas."""
    for slug in slugs:
        persona = store.load(slug)
        if persona is None:
            console.print(f"[red]Persona '{slug}' not found, skipping.[/red]")
            continue
        console.print(f"\n[bold]Refreshing: {slug}[/bold]")
        await run_research_pipeline(persona, store, slug)
