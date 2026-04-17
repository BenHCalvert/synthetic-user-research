"""synth init -- First-run setup wizard."""

import os
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from synth.models.config import AppConfig, ModelConfig, WebSearchConfig

console = Console()
CONFIG_DIR = Path.home() / ".config" / "synth-research"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

# Env var required for each provider
_MODEL_ENV_VARS: dict[str, tuple[str, str]] = {
    "anthropic": ("ANTHROPIC_API_KEY", "https://console.anthropic.com/"),
    "openai": ("OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
    "google": ("GOOGLE_API_KEY", "https://aistudio.google.com/app/apikey"),
}
_SEARCH_ENV_VARS: dict[str, tuple[str, str]] = {
    "tavily": ("TAVILY_API_KEY", "https://app.tavily.com/"),
    "serpapi": ("SERPAPI_API_KEY", "https://serpapi.com/manage-api-key"),
    "brave": ("BRAVE_API_KEY", "https://brave.com/search/api/"),
}


def _model_provider(model_id: str) -> str:
    """Infer provider name from a model ID string."""
    lower = model_id.lower()
    if lower.startswith("anthropic/") or lower.startswith("claude"):
        return "anthropic"
    if any(lower.startswith(p) for p in ("gpt", "openai/", "o1", "o3")):
        return "openai"
    if lower.startswith("gemini/") or lower.startswith("gemini"):
        return "google"
    return ""


def _print_key_status(models: list[ModelConfig], web_search: WebSearchConfig) -> list[str]:
    """Print an API key status table. Returns a list of missing env var names."""
    needed: dict[str, tuple[str, str]] = {}  # env_var -> (label, url)

    for m in models:
        provider = _model_provider(m.model_id)
        if provider in _MODEL_ENV_VARS:
            env, url = _MODEL_ENV_VARS[provider]
            needed[env] = (m.label, url)

    if web_search.provider in _SEARCH_ENV_VARS:
        env, url = _SEARCH_ENV_VARS[web_search.provider]
        needed[env] = (f"{web_search.provider} search", url)

    table = Table(title="API Key Status", show_header=True, header_style="bold")
    table.add_column("Key")
    table.add_column("Used for")
    table.add_column("Status")
    table.add_column("Where to get it")

    missing = []
    for env_var, (label, url) in needed.items():
        is_set = bool(os.environ.get(env_var))
        status = "[green]✓ set[/green]" if is_set else "[red]✗ missing[/red]"
        table.add_row(env_var, label, status, url if not is_set else "")
        if not is_set:
            missing.append(env_var)

    console.print()
    console.print(table)
    return missing


def _print_existing_config(config: AppConfig) -> None:
    """Print a summary of the existing configuration."""
    table = Table(title="Current Configuration", show_header=True, header_style="bold")
    table.add_column("Setting")
    table.add_column("Value")

    model_summary = ", ".join(f"{m.label} ({m.model_id})" for m in config.models)
    table.add_row("Models", model_summary or "(none)")
    table.add_row("Default panel models", str(config.default_model_count))
    table.add_row("Search provider", config.web_search.provider)

    console.print()
    console.print(table)


def init_command(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing config without prompting.")
    ] = False,
) -> None:
    """Set up synth-research: configure models and API keys."""
    console.print(
        Panel(
            "[bold]Welcome to synth-research[/bold]\n\n"
            "This wizard configures your model and search API preferences.\n"
            "API keys are read from environment variables -- this wizard just "
            "sets which models to use.",
            title="synth init",
        )
    )

    if CONFIG_PATH.exists() and not force:
        existing = AppConfig.load()
        _print_existing_config(existing)
        if not Confirm.ask("\nConfig already exists. Reconfigure?", default=False):
            console.print("[dim]Nothing changed.[/dim]")
            raise typer.Exit()

    models: list[ModelConfig] = []

    # Anthropic
    if Confirm.ask("Use Anthropic (Claude) models?", default=True):
        models.append(
            ModelConfig(
                model_id=Prompt.ask(
                    "Anthropic model ID",
                    default="anthropic/claude-sonnet-4-20250514",
                ),
                label="Claude",
            )
        )

    # OpenAI
    if Confirm.ask("Use OpenAI models?", default=True):
        models.append(
            ModelConfig(
                model_id=Prompt.ask("OpenAI model ID", default="gpt-4o"),
                label="GPT-4o",
            )
        )

    # Google
    if Confirm.ask("Use Google (Gemini) models?", default=False):
        models.append(
            ModelConfig(
                model_id=Prompt.ask("Google model ID", default="gemini/gemini-2.5-pro"),
                label="Gemini",
            )
        )

    if not models:
        console.print("[red]At least one model is required.[/red] Re-run `synth init`.")
        raise typer.Exit(code=1)

    # Default model count for panels
    default_count = min(2, len(models))
    default_count = int(
        Prompt.ask("Default number of models for panels", default=str(default_count))
    )

    # Web search
    web_search = WebSearchConfig()
    if Confirm.ask("Configure web search (for persona research)?", default=True):
        provider = Prompt.ask(
            "Search provider", choices=["tavily", "serpapi", "brave"], default="tavily"
        )
        web_search = WebSearchConfig(provider=provider)

    config = AppConfig(
        models=models,
        default_model_count=default_count,
        web_search=web_search,
    )

    # Write config
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        yaml.safe_dump(config.model_dump(), default_flow_style=False, sort_keys=False)
    )

    console.print(f"\n[green]Config written to {CONFIG_PATH}[/green]")

    missing_keys = _print_key_status(models, web_search)

    console.print("\n[bold]Next steps:[/bold]")
    if missing_keys:
        console.print("  1. Export missing API keys:")
        for key in missing_keys:
            console.print(f"       export {key}=...")
        console.print("  2. Run [bold]synth persona create[/bold] to build your first persona")
    else:
        console.print("  1. Run [bold]synth persona create[/bold] to build your first persona")
        console.print("  2. Run [bold]synth interview --persona <name> --topic <topic>[/bold]")
