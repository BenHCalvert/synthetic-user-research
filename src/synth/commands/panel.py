"""synth panel -- Multi-persona, multi-model synthetic panel."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()
panel_app = typer.Typer(help="Run synthetic panels.", invoke_without_command=True)


@panel_app.callback(invoke_without_command=True)
def panel(
    personas: str = typer.Option(None, help="Comma-separated persona slugs"),
    mode: str = typer.Option(
        None,
        help="Interview mode: problem-discovery, solution-feedback, "
        "concept-walkthrough, priority-ranking",
    ),
    topic: str = typer.Option(None, help="Panel topic or problem statement"),
    model_depth: str = typer.Option(
        "standard",
        help="Model depth: quick (1 model), standard (2), rigorous (3+)",
    ),
    preset: str = typer.Option(None, help="Panel preset name from .panels.yaml"),
    directory: Path = typer.Option(Path("personas"), help="Persona directory"),
    output_dir: Path = typer.Option(Path("reports"), help="Report output directory"),
) -> None:
    """Run a multi-persona, multi-model synthetic panel."""
    import asyncio

    from rich.prompt import Prompt

    from synth.core.panel_runner import run_panel
    from synth.core.persona_store import PersonaStore

    store = PersonaStore(directory)

    # Resolve preset
    persona_slugs: list[str] = []
    if preset:
        presets = store.load_presets()
        if preset not in presets:
            console.print(f"[red]Preset '{preset}' not found.[/red]")
            raise typer.Exit(code=1)
        persona_slugs = presets[preset]["personas"]
    elif personas:
        persona_slugs = [s.strip() for s in personas.split(",")]
    else:
        all_personas = store.list_all()
        if not all_personas:
            console.print("[red]No personas found.[/red] Run `synth persona create`.")
            raise typer.Exit(code=1)
        console.print("[bold]Available personas:[/bold]")
        for slug in all_personas:
            console.print(f"  - {slug}")
        raw = Prompt.ask("Persona slugs (comma-separated)")
        persona_slugs = [s.strip() for s in raw.split(",")]

    if not mode:
        mode = Prompt.ask(
            "Interview mode",
            choices=[
                "problem-discovery",
                "solution-feedback",
                "concept-walkthrough",
                "priority-ranking",
            ],
            default="problem-discovery",
        )

    if not topic:
        topic = Prompt.ask("Panel topic")

    asyncio.run(
        run_panel(
            persona_slugs=persona_slugs,
            mode=mode,
            topic=topic,
            model_depth=model_depth,
            store=store,
            output_dir=output_dir,
        )
    )
