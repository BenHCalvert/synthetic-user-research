"""synth interview -- Run single-persona synthetic interviews."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()
interview_app = typer.Typer(help="Run synthetic interviews.", invoke_without_command=True)


@interview_app.callback(invoke_without_command=True)
def interview(
    persona: str = typer.Option(None, help="Persona slug"),
    mode: str = typer.Option(
        None,
        help="Interview mode: problem-discovery, solution-feedback, "
        "concept-walkthrough, priority-ranking",
    ),
    topic: str = typer.Option(None, help="Interview topic or problem statement"),
    interactive: bool = typer.Option(False, help="Run in interactive mode"),
    model: str = typer.Option(None, help="Model label to use"),
    directory: Path = typer.Option(Path("personas"), help="Persona directory"),
    output_dir: Path = typer.Option(Path("transcripts"), help="Transcript output directory"),
) -> None:
    """Run a synthetic interview with a single persona."""
    import asyncio

    from rich.prompt import Prompt

    from synth.core.interviewer import run_interview
    from synth.core.persona_store import PersonaStore

    store = PersonaStore(directory)

    # Interactive prompts for missing args
    if not persona:
        personas = store.list_all()
        if not personas:
            console.print("[red]No personas found.[/red] Run `synth persona create`.")
            raise typer.Exit(code=1)
        console.print("[bold]Available personas:[/bold]")
        for slug in personas:
            console.print(f"  - {slug}")
        persona = Prompt.ask("Persona slug")

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
        topic = Prompt.ask("Interview topic")

    persona_data = store.load(persona)
    if not persona_data:
        console.print(f"[red]Persona '{persona}' not found.[/red]")
        raise typer.Exit(code=1)

    asyncio.run(
        run_interview(
            persona_data=persona_data,
            persona_slug=persona,
            mode=mode,
            topic=topic,
            interactive=interactive,
            model_label=model,
            output_dir=output_dir,
        )
    )
