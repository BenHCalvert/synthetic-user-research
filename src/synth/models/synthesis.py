"""Pydantic models for structured LLM output: synthesis reports, confidence tags, panel results."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Grounding(StrEnum):
    grounded = "grounded"
    plausible = "plausible"
    speculative = "speculative"


class ModelAgreement(StrEnum):
    converged = "converged"
    partial = "partial"
    diverged = "diverged"
    sycophancy_risk = "sycophancy_risk"
    single_model = "single_model"


class AdvocateStatus(StrEnum):
    challenged = "challenged"
    unchallenged = "unchallenged"


class ConfidenceTag(BaseModel):
    grounding: Grounding
    model_agreement: ModelAgreement
    advocate_status: AdvocateStatus


class Hypothesis(BaseModel):
    statement: str
    confidence: ConfidenceTag
    priority: str = Field(description="validate, monitor, or accept")
    validation_target: str | None = Field(
        default=None, description="Who to interview to validate this"
    )


class SynthesisReport(BaseModel):
    """Post-interview synthesis with confidence-tagged hypotheses."""

    themes: list[str]
    surprises: list[str]
    pushback_points: list[str]
    questions_for_real_interviews: list[str]
    hypotheses: list[Hypothesis]


class TriageEntry(BaseModel):
    """Per-persona, per-model reaction for the triage matrix."""

    persona_slug: str
    persona_name: str
    model_label: str
    reaction: str = Field(description="positive, mixed, or negative")
    summary: str


class ConvergentTheme(BaseModel):
    title: str
    confidence: ConfidenceTag
    description: str
    personas_who_raised: list[str]
    evidence_grounding: str


class DivergentTheme(BaseModel):
    title: str
    perspectives: dict[str, str] = Field(description="model_label -> perspective")
    interpretation: str


class PersonaDivergentTheme(BaseModel):
    title: str
    perspectives: dict[str, str] = Field(description="persona_slug -> their view")
    tension: str
    product_implication: str


class ChallengeReport(BaseModel):
    """Devil's advocate review output."""

    sycophancy_checks: list[str]
    missing_objections: list[str]
    ideal_user_assumptions: list[str]
    uncovered_edge_cases: list[str]
    challenged_themes: list[str] = Field(description="Theme titles that the advocate challenges")


class PanelResult(BaseModel):
    """Complete structured panel output."""

    topic: str
    date: str
    mode: str
    model_depth: str
    models_used: list[str]
    triage: list[TriageEntry]
    convergent_themes: list[ConvergentTheme]
    model_divergent_themes: list[DivergentTheme]
    persona_divergent_themes: list[PersonaDivergentTheme]
    blind_spots: list[str]
    advocate_addendum: ChallengeReport
    hypotheses: list[Hypothesis]
