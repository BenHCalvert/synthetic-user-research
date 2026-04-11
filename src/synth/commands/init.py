"""synth init -- First-run setup wizard."""

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from synth.models.config import AppConfig, ModelConfig, WebSearchConfig

console = Console()
CONFIG_DIR = Path.home() / ".config" / "synth-research"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


def init_command() -> None:
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
        yaml.dump(config.model_dump(), default_flow_style=False, sort_keys=False)
    )

    console.print(f"\n[green]Config written to {CONFIG_PATH}[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Set API key env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)")
    console.print("  2. Run [bold]synth persona create[/bold] to build your first persona")
