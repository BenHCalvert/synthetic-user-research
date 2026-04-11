"""Pydantic v2 models for the 3-layer persona schema."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

# --- Layer 1: Identity and Motivations (stable) ---


class JobToBeDone(BaseModel):
    """A single Job-to-Be-Done statement."""

    title: str
    when: str = Field(description="Situation or trigger")
    i_want_to: str = Field(description="Motivation")
    so_i_can: str = Field(description="Desired outcome")
    functional_success: str = Field(description="What 'done' looks like")
    emotional_success: str = Field(description="How they want to feel")
    social_success: str = Field(description="How they want to be perceived")


class IdentityAndMotivations(BaseModel):
    """Layer 1: Stable identity, JTBD, and fundamental motivations."""

    context: list[str] = Field(description="Role description, industry, setting")
    jobs_to_be_done: list[JobToBeDone] = Field(min_length=1)
    fundamental_motivations: list[str] = Field(
        min_length=2, max_length=4, description="Behaviors and values, NOT demographics"
    )


# --- Layer 2: Context and Constraints (semi-stable) ---


class TechnologyProfile(BaseModel):
    primary_device: str
    tech_comfort: str = Field(description="Specific capabilities, not 'digital native'")
    platform_stack: list[str] = Field(description="Tools they juggle daily")


class ChannelPreferences(BaseModel):
    preferred: list[str]
    avoided: list[str]


class TrustPosture(BaseModel):
    toward_product: str
    toward_technology: str
    specific_concerns: list[str]


class ContextAndConstraints(BaseModel):
    """Layer 2: Semi-stable context shaping behavior."""

    technology: TechnologyProfile
    channels: ChannelPreferences
    trust: TrustPosture


# --- Layer 3: Workflows and Pain Points (updates regularly) ---


class PainPoint(BaseModel):
    pain_point: str
    concrete_example: str
    severity: int = Field(ge=1, le=5)
    evidence: str = Field(description="Source citation or 'wizard-reported'")


class CrossRoleDependency(BaseModel):
    depends_on: list[str] = []
    depended_on_by: list[str] = []
    tension_points: list[str] = []


class WorkflowsAndPainPoints(BaseModel):
    """Layer 3: Workflows, pain points, and workarounds that change regularly."""

    typical_arc: list[str] = Field(description="Day/week interaction patterns")
    pain_points: list[PainPoint] = Field(min_length=1)
    compensating_behaviors: list[str] = Field(description="Workarounds and shadow systems")
    failure_modes: list[str]
    cross_role: CrossRoleDependency = CrossRoleDependency()


# --- Evidence and Provenance ---


class EvidenceAndProvenance(BaseModel):
    """Tracks what's grounded, what's inferred, what's unknown."""

    web_sources: list[str] = []
    key_findings: list[str] = []
    app_reviews_analyzed: str | None = None
    key_complaints: list[str] = []
    thin_data_areas: list[str] = Field(description="LLM must NOT invent detail here")
    assumed_but_unverified: list[str] = []
    representativeness_note: str = ""


# --- Simulation Controls ---


class VoiceAndTone(BaseModel):
    speaking_style: str
    vocabulary_level: str
    emotional_baseline: str


class SimulationControls(BaseModel):
    """Directives that shape how the LLM roleplays this persona."""

    voice: VoiceAndTone
    hard_constraints: list[str] = Field(min_length=1)
    abstention_rules: list[str] = Field(min_length=1)
    anti_sycophancy_directives: list[str] = Field(min_length=1)


# --- Top-level Persona Model ---


class RefreshSource(BaseModel):
    source: str
    date: date
    scope: str = ""


class ChangelogEntry(BaseModel):
    date: date
    change: str


class PersonaModel(BaseModel):
    """Complete persona schema: frontmatter + 3 layers + evidence + simulation controls."""

    # Frontmatter
    persona: str = Field(description="Human-readable persona name")
    role: str = Field(description="User-defined role, not an enum")
    sub_role: str = ""
    archetype_label: str = Field(description="e.g., 'The Overwhelmed Gatekeeper'")
    version: float = 1.0
    last_refreshed: date = Field(default_factory=date.today)
    staleness_threshold_days: int = 90
    refresh_sources: list[RefreshSource] = []
    changelog: list[ChangelogEntry] = []

    # Layers
    identity: IdentityAndMotivations
    context: ContextAndConstraints
    workflows: WorkflowsAndPainPoints

    # Evidence and simulation
    evidence: EvidenceAndProvenance
    simulation: SimulationControls


class DomainContext(BaseModel):
    """Shared domain context for all personas in a project."""

    domain: str
    product_name: str = ""
    research_sources: dict[str, list[str] | str] = Field(default_factory=dict)
    user_roles: list[str] = []
    key_frustrations: list[str] = []
    user_segments: list[str] = []
    data_sources: list[str] = []
