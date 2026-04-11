"""Cross-persona and cross-model synthesis engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from rich.console import Console

from synth.models.synthesis import (
    ConvergentTheme,
    DivergentTheme,
    PersonaDivergentTheme,
    SynthesisReport,
    TriageEntry,
)

console = Console()

if TYPE_CHECKING:
    from synth.core.llm import LLM


class PanelSynthesizer:
    """Synthesizes results across personas and models into a panel report."""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def synthesize_per_model(
        self,
        model_label: str,
        per_persona_results: dict[str, SynthesisReport],
    ) -> dict[str, str]:
        """Summarize themes across personas for a single model."""
        summaries: dict[str, str] = {}
        for slug, report in per_persona_results.items():
            themes_text = "\n".join(f"- {t}" for t in report.themes)
            pushback_text = "\n".join(f"- {p}" for p in report.pushback_points)
            summaries[slug] = f"Themes:\n{themes_text}\n\nPushback:\n{pushback_text}"
        return summaries

    async def build_triage(
        self,
        all_results: dict[str, dict[str, SynthesisReport]],
        persona_names: dict[str, str],
    ) -> list[TriageEntry]:
        """Build the persona x model triage matrix."""
        entries: list[TriageEntry] = []
        for slug, model_results in all_results.items():
            for model_label, report in model_results.items():
                # Determine reaction from themes and pushback
                pushback_count = len(report.pushback_points)
                if pushback_count >= 3:
                    reaction = "negative"
                elif pushback_count >= 1:
                    reaction = "mixed"
                else:
                    reaction = "positive"

                entries.append(
                    TriageEntry(
                        persona_slug=slug,
                        persona_name=persona_names.get(slug, slug),
                        model_label=model_label,
                        reaction=reaction,
                        summary="; ".join(report.themes[:2]),
                    )
                )
        return entries

    async def find_convergent_themes(
        self,
        all_results: dict[str, dict[str, SynthesisReport]],
        model_label: str,
    ) -> list[ConvergentTheme]:
        """Find themes that emerged across 3+ personas and across models via LLM."""
        # Collect all themes with their sources
        all_themes_text = []
        for slug, model_results in all_results.items():
            for ml, report in model_results.items():
                for theme in report.themes:
                    all_themes_text.append(f"[{slug}/{ml}] {theme}")

        system = (
            "You are a research analyst. Given these themes from multiple personas "
            "and models, identify convergent themes that appear across 3+ sources. "
            "Return structured data."
        )
        messages = [
            {
                "role": "user",
                "content": "Themes:\n" + "\n".join(all_themes_text),
            }
        ]

        # Use LLM for rich analysis, fall back to empty on LLM/parse errors
        try:
            result = await self.llm.structured_complete(
                system,
                messages,
                model_label,
                _ConvergentThemeList,
            )
            return result.themes  # type: ignore[return-value]
        except (ValueError, RuntimeError) as e:
            console.print(f"[yellow]Convergent theme analysis failed: {e}[/yellow]")
            return []

    async def find_divergent_themes(
        self,
        all_results: dict[str, dict[str, SynthesisReport]],
        model_label: str,
    ) -> tuple[list[DivergentTheme], list[PersonaDivergentTheme]]:
        """Find themes where models or personas disagree."""
        all_data = []
        for slug, model_results in all_results.items():
            for ml, report in model_results.items():
                all_data.append(
                    f"[{slug}/{ml}] Themes: {report.themes}, Pushback: {report.pushback_points}"
                )

        system = (
            "You are a research analyst. Identify where models disagree about the "
            "same persona (model-divergent) and where personas disagree with each "
            "other (persona-divergent). Return structured data."
        )
        messages = [{"role": "user", "content": "\n".join(all_data)}]

        try:
            result = await self.llm.structured_complete(
                system, messages, model_label, _DivergenceResult
            )
            return result.model_divergent, result.persona_divergent  # type: ignore[return-value]
        except (ValueError, RuntimeError) as e:
            console.print(f"[yellow]Divergence analysis failed: {e}[/yellow]")
            return [], []


# Helper models for structured LLM output during synthesis


class _ConvergentThemeList(BaseModel):
    themes: list[ConvergentTheme]


class _DivergenceResult(BaseModel):
    model_divergent: list[DivergentTheme]
    persona_divergent: list[PersonaDivergentTheme]
