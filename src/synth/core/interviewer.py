"""Single-persona interview engine: system prompt construction, interactive + autonomous modes."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from synth.core.interview_guide import INTERVIEW_GUIDES, INTERVIEW_RULES
from synth.core.llm import LLM
from synth.models.config import AppConfig
from synth.models.synthesis import SynthesisReport

if TYPE_CHECKING:
    from synth.models.persona import PersonaModel

console = Console()


def _build_system_prompt(persona: PersonaModel, mode: str) -> str:
    """Construct the full system prompt from persona + interview guide."""
    persona_yaml = yaml.safe_dump(
        persona.model_dump(mode="json"), default_flow_style=False, sort_keys=False
    )

    anti_syc = "\n".join(f"- {d}" for d in persona.simulation.anti_sycophancy_directives)

    return f"""You are roleplaying as {persona.persona}, a {persona.archetype_label}.

=== YOUR PROFILE ===
{persona_yaml}

=== YOUR EVIDENCE BASE ===
Pain points and examples from your experience:
{chr(10).join(f"- {pp.pain_point}: {pp.concrete_example}" for pp in persona.workflows.pain_points)}

Workarounds you use:
{chr(10).join(f"- {w}" for w in persona.workflows.compensating_behaviors)}

{INTERVIEW_RULES}

=== ANTI-SYCOPHANCY ===
{anti_syc}
"""


def _check_staleness(persona: PersonaModel) -> None:
    """Warn if persona data is stale."""
    threshold = persona.last_refreshed + timedelta(days=persona.staleness_threshold_days)
    if date.today() > threshold:
        console.print(
            f"[yellow]Warning: Persona '{persona.persona}' was last refreshed "
            f"{persona.last_refreshed}. Consider running `synth persona refresh`.[/yellow]"
        )


async def _run_autonomous_interview(
    llm: LLM,
    system_prompt: str,
    persona: PersonaModel,
    mode: str,
    topic: str,
    model_label: str,
) -> list[dict[str, str]]:
    """Run a full autonomous interview using the interview guide."""
    guide = INTERVIEW_GUIDES[mode]
    transcript: list[dict[str, str]] = []

    # Opening question
    opening = str(guide["opening"]).format(topic=topic)
    transcript.append({"role": "user", "content": opening})
    console.print(f"\n[bold cyan]Interviewer:[/bold cyan] {opening}")

    response = await llm.complete(system_prompt, transcript, model_label)
    transcript.append({"role": "assistant", "content": response})
    console.print(f"\n[bold green]{persona.persona}:[/bold green] {response}")

    # Core questions
    core_questions = list(guide["core_questions"])
    for question_template in core_questions:
        question = question_template.format(topic=topic)
        transcript.append({"role": "user", "content": question})
        console.print(f"\n[bold cyan]Interviewer:[/bold cyan] {question}")

        response = await llm.complete(system_prompt, transcript, model_label)
        transcript.append({"role": "assistant", "content": response})
        console.print(f"\n[bold green]{persona.persona}:[/bold green] {response}")

    # Anti-sycophancy probes
    probes = list(guide["anti_sycophancy_probes"])
    for probe_template in probes:
        probe = probe_template.format(topic=topic)
        transcript.append({"role": "user", "content": probe})
        console.print(f"\n[bold cyan]Interviewer:[/bold cyan] {probe}")

        response = await llm.complete(system_prompt, transcript, model_label)
        transcript.append({"role": "assistant", "content": response})
        console.print(f"\n[bold green]{persona.persona}:[/bold green] {response}")

    return transcript


async def _run_interactive_interview(
    llm: LLM,
    system_prompt: str,
    persona: PersonaModel,
    model_label: str,
) -> list[dict[str, str]]:
    """Run an interactive interview where the user types questions."""
    transcript: list[dict[str, str]] = []
    console.print(
        Panel(
            f"[bold]Interactive interview with {persona.persona}[/bold]\n"
            "Type your questions. Enter 'done' to finish.",
            title="Interview",
        )
    )

    while True:
        question = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        if question.lower() in ("done", "quit", "exit"):
            break

        transcript.append({"role": "user", "content": question})
        response = await llm.complete(system_prompt, transcript, model_label)
        transcript.append({"role": "assistant", "content": response})
        console.print(f"\n[bold green]{persona.persona}:[/bold green] {response}")

    return transcript


async def _synthesize_interview(
    llm: LLM,
    transcript: list[dict[str, str]],
    persona: PersonaModel,
    model_label: str,
) -> SynthesisReport:
    """Generate a post-interview synthesis with confidence tags."""
    transcript_text = "\n\n".join(
        f"**{'Interviewer' if m['role'] == 'user' else persona.persona}**: {m['content']}"
        for m in transcript
    )

    system = (
        "You are a user research analyst. Analyze this synthetic interview transcript "
        "and produce a structured synthesis. Be honest about what's speculative vs. grounded. "
        "Remember: this is SYNTHETIC data -- tag everything appropriately."
    )
    messages = [
        {
            "role": "user",
            "content": f"Analyze this interview transcript:\n\n{transcript_text}",
        }
    ]

    return await llm.structured_complete(  # type: ignore[return-value]
        system, messages, model_label, SynthesisReport
    )


def _save_transcript(
    transcript: list[dict[str, str]],
    synthesis: SynthesisReport,
    persona: PersonaModel,
    persona_slug: str,
    mode: str,
    topic: str,
    model_label: str,
    output_dir: Path,
) -> Path:
    """Save interview transcript and synthesis as Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filename = f"{today}_{persona_slug}_{mode}.md"
    path = output_dir / filename

    lines = [
        "# Synthetic Interview Transcript\n",
        "> SYNTHETIC -- Treat as hypothesis, not evidence.\n",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Persona** | {persona.persona} ({persona.archetype_label}) |",
        f"| **Mode** | {mode} |",
        f"| **Topic** | {topic} |",
        f"| **Model** | {model_label} |",
        f"| **Date** | {today} |\n",
        "---\n",
    ]

    for msg in transcript:
        speaker = "Interviewer" if msg["role"] == "user" else persona.persona
        lines.append(f"**{speaker}**: {msg['content']}\n")

    lines.append("\n---\n")
    lines.append("## Synthesis\n")
    lines.append("### Key Themes")
    for i, theme in enumerate(synthesis.themes, 1):
        lines.append(f"{i}. {theme}")
    lines.append("\n### Surprises")
    for s in synthesis.surprises:
        lines.append(f"- {s}")
    lines.append("\n### Pushback Points")
    for p in synthesis.pushback_points:
        lines.append(f"- {p}")
    lines.append("\n### Questions for Real Interviews")
    for q in synthesis.questions_for_real_interviews:
        lines.append(f"- {q}")
    lines.append("\n### Hypotheses")
    for h in synthesis.hypotheses:
        lines.append(
            f"- **{h.statement}** [{h.confidence.grounding.value}, "
            f"{h.confidence.model_agreement.value}, "
            f"{h.confidence.advocate_status.value}] → {h.priority}"
        )

    path.write_text("\n".join(lines))
    return path


async def run_interview(
    persona_data: PersonaModel,
    persona_slug: str,
    mode: str,
    topic: str,
    interactive: bool = False,
    model_label: str | None = None,
    output_dir: Path = Path("transcripts"),
) -> SynthesisReport:
    """Run a complete synthetic interview."""
    _check_staleness(persona_data)

    config = AppConfig.load()
    llm = LLM(config.models)

    if model_label is None:
        model_label = llm.available_labels[0]

    system_prompt = _build_system_prompt(persona_data, mode)

    console.print(
        Panel(
            f"[bold]{persona_data.persona}[/bold] ({persona_data.archetype_label})\n"
            f"Mode: {mode} | Model: {model_label}\n"
            f"Topic: {topic}",
            title="Synthetic Interview",
            subtitle="SYNTHETIC -- Treat as hypothesis, not evidence",
        )
    )

    if interactive:
        transcript = await _run_interactive_interview(llm, system_prompt, persona_data, model_label)
    else:
        transcript = await _run_autonomous_interview(
            llm, system_prompt, persona_data, mode, topic, model_label
        )

    # Synthesis
    console.print("\n[bold]Generating synthesis...[/bold]")
    synthesis = await _synthesize_interview(llm, transcript, persona_data, model_label)

    # Display synthesis
    console.print(
        Panel(
            Markdown("### Themes\n" + "\n".join(f"- {t}" for t in synthesis.themes)),
            title="Synthesis",
        )
    )

    # Save
    path = _save_transcript(
        transcript,
        synthesis,
        persona_data,
        persona_slug,
        mode,
        topic,
        model_label,
        output_dir,
    )
    console.print(f"\n[green]Transcript saved to {path}[/green]")

    return synthesis
