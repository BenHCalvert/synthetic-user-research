"""Panel engine: multi-persona x multi-model dispatch and report generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from synth.core.advocate import apply_advocate_challenges, run_advocate_pass
from synth.core.interviewer import (
    _build_system_prompt,
    _run_autonomous_interview,
    _synthesize_interview,
)
from synth.core.llm import LLM
from synth.core.synthesizer import PanelSynthesizer
from synth.models.config import AppConfig
from synth.models.synthesis import (
    Hypothesis,
    PanelResult,
    SynthesisReport,
)

if TYPE_CHECKING:
    from synth.core.persona_store import PersonaStore
    from synth.models.persona import PersonaModel

console = Console()

MODEL_DEPTH_MAP = {
    "quick": 1,
    "standard": 2,
    "rigorous": 3,
}


def _select_models(llm: LLM, depth: str) -> list[str]:
    """Select models based on depth setting."""
    count = MODEL_DEPTH_MAP.get(depth, 2)
    labels = llm.available_labels
    return labels[: min(count, len(labels))]


async def run_panel(
    persona_slugs: list[str],
    mode: str,
    topic: str,
    model_depth: str,
    store: PersonaStore,
    output_dir: Path = Path("reports"),
) -> PanelResult:
    """Run a full multi-persona, multi-model synthetic panel."""
    config = AppConfig.load()
    llm = LLM(config.models)
    model_labels = _select_models(llm, model_depth)
    synthesizer = PanelSynthesizer(llm)

    # Load personas
    personas: dict[str, PersonaModel] = {}
    for slug in persona_slugs:
        persona = store.load(slug)
        if persona is None:
            console.print(f"[red]Persona '{slug}' not found, skipping.[/red]")
            continue
        personas[slug] = persona

    if not personas:
        console.print("[red]No valid personas loaded.[/red]")
        raise RuntimeError("No valid personas loaded for panel")

    console.print(
        Panel(
            f"[bold]Synthetic Panel[/bold]\n"
            f"Topic: {topic}\n"
            f"Mode: {mode}\n"
            f"Personas: {', '.join(personas.keys())}\n"
            f"Models: {', '.join(model_labels)} ({model_depth})\n",
            title="synth panel",
            subtitle="SYNTHETIC -- Treat as hypothesis, not evidence",
        )
    )

    # Run interviews: persona x model
    # all_results[slug][model_label] = SynthesisReport
    all_results: dict[str, dict[str, SynthesisReport]] = {}
    persona_names: dict[str, str] = {}

    total = len(personas) * len(model_labels)
    with Progress(console=console) as progress:
        task = progress.add_task("Running interviews...", total=total)

        for slug, persona in personas.items():
            persona_names[slug] = persona.persona
            all_results[slug] = {}
            system_prompt = _build_system_prompt(persona, mode)

            for model_label in model_labels:
                progress.update(task, description=f"{slug} x {model_label}")

                transcript = await _run_autonomous_interview(
                    llm, system_prompt, persona, mode, topic, model_label
                )
                synthesis = await _synthesize_interview(llm, transcript, persona, model_label)
                all_results[slug][model_label] = synthesis
                progress.advance(task)

    # Build triage matrix
    triage = await synthesizer.build_triage(all_results, persona_names)

    # Display triage
    triage_table = Table(title="Triage Matrix")
    triage_table.add_column("Persona", style="bold")
    for ml in model_labels:
        triage_table.add_column(ml)
    triage_table.add_column("Agreement")

    for slug in personas:
        row_reactions = []
        for ml in model_labels:
            entries = [e for e in triage if e.persona_slug == slug and e.model_label == ml]
            row_reactions.append(entries[0].reaction if entries else "?")

        agreement = "converged" if len(set(row_reactions)) == 1 else "diverged"
        triage_table.add_row(persona_names[slug], *row_reactions, agreement)

    console.print(triage_table)

    # Cross-model analysis
    primary_model = model_labels[0]
    convergent = await synthesizer.find_convergent_themes(all_results, primary_model)
    model_divergent, persona_divergent = await synthesizer.find_divergent_themes(
        all_results, primary_model
    )

    # Collect all hypotheses
    all_hypotheses: list[Hypothesis] = []
    for slug_results in all_results.values():
        for report in slug_results.values():
            all_hypotheses.extend(report.hypotheses)

    # Devil's advocate pass
    console.print("\n[bold]Running devil's advocate review...[/bold]")
    findings_text = _format_findings_for_advocate(all_results, persona_names)
    advocate_report = await run_advocate_pass(llm, findings_text, primary_model)

    # Apply challenges to hypotheses
    all_hypotheses = apply_advocate_challenges(all_hypotheses, advocate_report)

    # Identify blind spots
    blind_spots = [
        f"Weak reaction from {slug}"
        for slug, model_results in all_results.items()
        if all(len(r.themes) <= 1 for r in model_results.values())
    ]

    # Build panel result
    result = PanelResult(
        topic=topic,
        date=date.today().isoformat(),
        mode=mode,
        model_depth=model_depth,
        models_used=model_labels,
        triage=triage,
        convergent_themes=convergent,
        model_divergent_themes=model_divergent,
        persona_divergent_themes=persona_divergent,
        blind_spots=blind_spots,
        advocate_addendum=advocate_report,
        hypotheses=all_hypotheses,
    )

    # Save report
    report_path = _save_panel_report(result, persona_names, output_dir)
    console.print(f"\n[green]Panel report saved to {report_path}[/green]")

    return result


def _format_findings_for_advocate(
    all_results: dict[str, dict[str, SynthesisReport]],
    persona_names: dict[str, str],
) -> str:
    """Format all findings into text for the advocate review."""
    sections = []
    for slug, model_results in all_results.items():
        name = persona_names.get(slug, slug)
        for model_label, report in model_results.items():
            themes = "\n".join(f"  - {t}" for t in report.themes)
            pushback = "\n".join(f"  - {p}" for p in report.pushback_points)
            sections.append(
                f"### {name} ({model_label})\nThemes:\n{themes}\nPushback:\n{pushback}\n"
            )
    return "\n".join(sections)


def _save_panel_report(
    result: PanelResult,
    persona_names: dict[str, str],
    output_dir: Path,
) -> Path:
    """Generate and save a Markdown panel report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{result.date}_panel_{result.mode}.md"
    path = output_dir / filename

    lines = [
        "# Synthetic Panel Report\n",
        "> **SYNTHETIC RESEARCH -- Treat all findings as hypotheses to validate, "
        "not as evidence.**",
        f"> Generated by `synth panel` on {result.date}.\n",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Topic** | {result.topic} |",
        f"| **Interview mode** | {result.mode} |",
        f"| **Personas interviewed** | {', '.join(persona_names.values())} |",
        f"| **Model depth** | {result.model_depth} |",
        f"| **Models used** | {', '.join(result.models_used)} |\n",
        "---\n",
        "## 1. Triage Matrix\n",
    ]

    # Triage table
    model_headers = " | ".join(result.models_used)
    lines.append(f"| Persona | {model_headers} | Agreement |")
    lines.append("|" + "---------|" * (len(result.models_used) + 2))

    slug_reactions: dict[str, dict[str, str]] = {}
    for entry in result.triage:
        slug_reactions.setdefault(entry.persona_slug, {})[entry.model_label] = entry.reaction

    for slug, reactions in slug_reactions.items():
        name = persona_names.get(slug, slug)
        cells = [reactions.get(ml, "?") for ml in result.models_used]
        agreement = "converged" if len(set(cells)) == 1 else "diverged"
        lines.append(f"| {name} | {' | '.join(cells)} | {agreement} |")

    lines.append("")

    # Convergent themes
    lines.append("## 2. Convergent Themes\n")
    for theme in result.convergent_themes:
        lines.append(f"### Theme: {theme.title}")
        lines.append(
            f"**Confidence**: [{theme.confidence.grounding.value}, "
            f"{theme.confidence.model_agreement.value}, "
            f"{theme.confidence.advocate_status.value}]"
        )
        lines.append(f"{theme.description}")
        lines.append(f"**Personas who raised this**: {', '.join(theme.personas_who_raised)}")
        lines.append(f"**Evidence grounding**: {theme.evidence_grounding}\n")

    # Model-divergent themes
    lines.append("## 3. Model-Divergent Themes\n")
    for theme in result.model_divergent_themes:
        lines.append(f"### Theme: {theme.title}")
        for model, perspective in theme.perspectives.items():
            lines.append(f"**{model} perspective**: {perspective}")
        lines.append(f"**Interpretation**: {theme.interpretation}\n")

    # Persona-divergent themes
    lines.append("## 4. Persona-Divergent Themes\n")
    for theme in result.persona_divergent_themes:
        lines.append(f"### Theme: {theme.title}")
        for persona, view in theme.perspectives.items():
            lines.append(f"**{persona} says**: {view}")
        lines.append(f"**Tension**: {theme.tension}")
        lines.append(f"**Product implication**: {theme.product_implication}\n")

    # Blind spots
    lines.append("## 5. Blind Spots\n")
    if result.blind_spots:
        for bs in result.blind_spots:
            lines.append(f"- {bs}")
    else:
        lines.append("No significant blind spots identified.\n")

    # Devil's advocate addendum
    lines.append("\n## 6. Devil's Advocate Addendum\n")
    adv = result.advocate_addendum
    lines.append("### Sycophancy Checks")
    for s in adv.sycophancy_checks:
        lines.append(f"- {s}")
    lines.append("\n### Missing Objections")
    for m in adv.missing_objections:
        lines.append(f"- {m}")
    lines.append("\n### Ideal-User Assumptions")
    for a in adv.ideal_user_assumptions:
        lines.append(f"- {a}")
    lines.append("\n### Uncovered Edge Cases")
    for e in adv.uncovered_edge_cases:
        lines.append(f"- {e}")

    # Hypotheses table
    lines.append("\n## 7. Confidence-Tagged Hypotheses\n")
    lines.append("| # | Hypothesis | Grounding | Model Agreement | Advocate Status | Priority |")
    lines.append("|---|-----------|-----------|-----------------|-----------------|----------|")
    for i, h in enumerate(result.hypotheses, 1):
        lines.append(
            f"| {i} | {h.statement} | {h.confidence.grounding.value} | "
            f"{h.confidence.model_agreement.value} | "
            f"{h.confidence.advocate_status.value} | {h.priority} |"
        )

    path.write_text("\n".join(lines))
    return path
