"""Typer CLI entry point for synth-research."""

import typer

from synth.commands.init import init_command
from synth.commands.interview import interview_app
from synth.commands.panel import panel_app
from synth.commands.persona import persona_app

app = typer.Typer(
    name="synth",
    help="AI-simulated user research with evidence-grounded personas.",
    no_args_is_help=True,
)

app.command(name="init")(init_command)
app.add_typer(persona_app, name="persona")
app.add_typer(interview_app, name="interview")
app.add_typer(panel_app, name="panel")

if __name__ == "__main__":
    app()
