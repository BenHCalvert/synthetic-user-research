"""synth persona -- Create, list, research, and refresh personas."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from synth.core.persona_store import PersonaStore

console = Console()
persona_app = typer.Typer(
    help="Create, list, research, and refresh personas.", no_args_is_help=True
)


@persona_app.command("list")
def list_personas(
    directory: Path = typer.Option(Path("personas"), help="Persona directory"),
) -> None:
    """List all personas in the project."""
    store = PersonaStore(directory)
    personas = store.list_all()

    if not personas:
        console.print("[yellow]No personas found.[/yellow] Run `synth persona create`.")
        return

    table = Table(title="Personas")
    table.add_column("Slug", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Role")
    table.add_column("Archetype")
    table.add_column("Version")
    table.add_column("Last Refreshed")

    for slug, persona in personas.items():
        table.add_row(
            slug,
            persona.persona,
            persona.role,
            persona.archetype_label,
            str(persona.version),
            str(persona.last_refreshed),
        )

    console.print(table)


@persona_app.command("create")
def create_persona(
    directory: Path = typer.Option(Path("personas"), help="Persona directory"),
) -> None:
    """Interactive wizard to create a new persona."""
    from synth.wizard.persona_wizard import run_persona_wizard

    run_persona_wizard(directory)


@persona_app.command("research")
def research_persona(
    slug: str = typer.Argument(help="Persona slug to research"),
    directory: Path = typer.Option(Path("personas"), help="Persona directory"),
) -> None:
    """Enrich a persona with web research."""
    import asyncio

    from synth.core.persona_store import PersonaStore
    from synth.research.pipeline import run_research_pipeline

    store = PersonaStore(directory)
    persona = store.load(slug)
    if not persona:
        console.print(f"[red]Persona '{slug}' not found.[/red]")
        raise typer.Exit(code=1)

    asyncio.run(run_research_pipeline(persona, store, slug))


@persona_app.command("refresh")
def refresh_persona(
    slug: str = typer.Argument(None, help="Persona slug to refresh (or --all)"),
    all_personas: bool = typer.Option(False, "--all", help="Refresh all personas"),
    directory: Path = typer.Option(Path("personas"), help="Persona directory"),
) -> None:
    """Re-research and update existing personas."""
    import asyncio

    from synth.core.persona_store import PersonaStore
    from synth.research.pipeline import run_refresh_pipeline

    store = PersonaStore(directory)

    if all_personas:
        slugs = list(store.list_all().keys())
    elif slug:
        slugs = [slug]
    else:
        console.print("[red]Provide a persona slug or use --all.[/red]")
        raise typer.Exit(code=1)

    asyncio.run(run_refresh_pipeline(slugs, store))
