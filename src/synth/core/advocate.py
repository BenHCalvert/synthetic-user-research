"""Devil's advocate engine: adversarial review of panel findings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synth.models.synthesis import (
    AdvocateStatus,
    ChallengeReport,
    ConfidenceTag,
    Hypothesis,
)

if TYPE_CHECKING:
    from synth.core.llm import LLM

ADVOCATE_SYSTEM_PROMPT = """You are a skeptical reviewer of synthetic user research findings. Your job is to challenge overly smooth consensus and catch sycophantic LLM behavior.

For each theme and hypothesis presented to you:
1. Ask: "What would make a REAL user push back on this?"
2. Check for sycophancy: Did personas agree too easily? Did they fail to mention switching costs, learning curves, or inertia?
3. Check for ideal-user bias: Are the findings assuming motivated, tech-savvy, change-ready users?
4. Check for missing objections: What obvious concerns were never raised?
5. Check for uncovered edge cases: What happens when things go wrong, when users are distracted, when data is messy?

Be specific. Name the themes you're challenging. Explain WHY they're suspicious.

Remember: synthetic research systematically over-estimates enthusiasm and under-estimates friction. Your job is to correct for that bias."""


async def run_advocate_pass(
    llm: LLM,
    findings_text: str,
    model_label: str,
) -> ChallengeReport:
    """Run the devil's advocate adversarial review pass."""
    messages = [
        {
            "role": "user",
            "content": (
                "Review these synthetic research findings for sycophancy, "
                "missing objections, and ideal-user assumptions:\n\n"
                f"{findings_text}"
            ),
        }
    ]

    return await llm.structured_complete(  # type: ignore[return-value]
        ADVOCATE_SYSTEM_PROMPT,
        messages,
        model_label,
        ChallengeReport,
    )


def apply_advocate_challenges(
    hypotheses: list[Hypothesis],
    challenge_report: ChallengeReport,
) -> list[Hypothesis]:
    """Update hypothesis confidence tags based on advocate challenges."""
    challenged_titles = set(t.lower().strip() for t in challenge_report.challenged_themes)

    updated: list[Hypothesis] = []
    for h in hypotheses:
        if any(ct in h.statement.lower() for ct in challenged_titles):
            new_confidence = ConfidenceTag(
                grounding=h.confidence.grounding,
                model_agreement=h.confidence.model_agreement,
                advocate_status=AdvocateStatus.challenged,
            )
            updated.append(h.model_copy(update={"confidence": new_confidence}))
        else:
            updated.append(h)

    return updated
