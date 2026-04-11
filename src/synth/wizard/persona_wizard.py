"""Guided persona creation wizard using Rich interactive prompts."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from synth.core.llm import LLM
from synth.core.persona_store import PersonaStore
from synth.models.config import AppConfig
from synth.models.persona import (
    ChangelogEntry,
    ChannelPreferences,
    ContextAndConstraints,
    DomainContext,
    EvidenceAndProvenance,
    IdentityAndMotivations,
    JobToBeDone,
    PainPoint,
    PersonaModel,
    SimulationControls,
    TechnologyProfile,
    TrustPosture,
    VoiceAndTone,
    WorkflowsAndPainPoints,
)

console = Console()

WIZARD_SYNTHESIS_PROMPT = """You are a user research expert creating a persona file.

The user provided these answers about their product and this user role:
{wizard_answers}

Generate a complete persona following the PersonaModel schema. Requirements:
- Convert informal answers into structured JTBD statements (When/I want to/So I can)
- Generate 3-5 pain points with concrete examples extrapolated from the user's descriptions
- Write Simulation Controls with persona-specific voice, vocabulary, and anti-sycophancy directives
- In Known Gaps, list everything the user said they were unsure about or had no data for
- Mark evidence quality: "wizard-reported" for things the user stated confidently, "wizard-inferred" for things you extrapolated, "unknown" for gaps
- The anti-sycophancy directives must reference this specific persona's workarounds and skepticism patterns, not generic pushback language
- Make the voice and tone section specific to this persona's industry and role
"""


def _ask_multi(prompt: str) -> list[str]:
    """Ask for a comma-separated list."""
    raw = Prompt.ask(prompt)
    return [s.strip() for s in raw.split(",") if s.strip()]


def _collect_domain_context(store: PersonaStore) -> DomainContext:
    """Phase 1: Collect domain context shared by all personas."""
    existing = store.load_domain_context()
    if existing and not Confirm.ask("Domain context exists. Re-enter?", default=False):
        return existing

    console.print(
        Panel(
            "[bold]Phase 1: Domain Context[/bold]\nTell me about your product and users.",
            title="Wizard",
        )
    )

    domain = Prompt.ask("What product or service are you building personas for?")
    product_name = Prompt.ask("Product name (if any)", default="")
    roles = _ask_multi("Who are the main types of users? List their roles (comma-separated)")
    frustrations = _ask_multi(
        "Main frustrations or pain points you've heard about (comma-separated)"
    )
    segments = _ask_multi(
        "Different user segments with different needs? (comma-separated, or 'none')"
    )
    data_sources = _ask_multi("What data sources do you have? (support tickets, interviews, etc.)")

    ctx = DomainContext(
        domain=domain,
        product_name=product_name,
        user_roles=roles,
        key_frustrations=frustrations,
        user_segments=segments if segments != ["none"] else [],
        data_sources=data_sources,
    )
    store.save_domain_context(ctx)
    console.print("[green]Domain context saved.[/green]")
    return ctx


def _collect_persona_answers(role: str, domain: DomainContext) -> dict[str, str]:
    """Phase 2: Collect per-persona interview answers."""
    console.print(
        Panel(
            f"[bold]Phase 2: Persona for '{role}'[/bold]\nProduct: {domain.domain}",
            title="Wizard",
        )
    )

    answers: dict[str, str] = {"role": role, "domain": domain.domain}

    # Layer 1
    console.print("\n[bold]Identity and Motivations[/bold]")
    answers["day_description"] = Prompt.ask(
        f"Describe a typical person in the '{role}' role. What's their day like?"
    )
    answers["main_jobs"] = Prompt.ask(
        "What are the 2-3 main jobs they're trying to do with your product?"
    )
    answers["success_failure"] = Prompt.ask(
        "What does success look like for them? What does failure look like?"
    )

    # Layer 2
    console.print("\n[bold]Context and Constraints[/bold]")
    answers["tech_savvy"] = Prompt.ask("How tech-savvy are they? What devices do they use?")
    answers["competing_tools"] = Prompt.ask("What other tools compete for their attention?")
    answers["constraints"] = Prompt.ask(
        "What constraints shape their behavior? (time, budget, org politics, etc.)"
    )

    # Layer 3
    console.print("\n[bold]Workflows and Pain Points[/bold]")
    answers["biggest_frustration"] = Prompt.ask(
        "What's the biggest frustration for this user type?"
    )
    answers["workarounds"] = Prompt.ask("What workarounds do they use when the product fails them?")
    answers["cascade_effects"] = Prompt.ask(
        "Who else is affected when things go wrong for this user?"
    )

    # Evidence quality
    console.print("\n[bold]Evidence Quality[/bold]")
    answers["confidence"] = Prompt.ask(
        "How confident are you in these answers? (real data / gut feel / mixed)"
    )
    answers["unknown"] = Prompt.ask("What don't you know about this user type?")

    return answers


def _synthesize_with_llm(answers: dict[str, str], domain: DomainContext) -> PersonaModel:
    """Use LLM to synthesize wizard answers into a complete persona."""
    config = AppConfig.load()
    if not config.models:
        raise RuntimeError("No models configured. Run `synth init` first.")

    import asyncio

    llm = LLM(config.models)
    model_label = llm.available_labels[0]

    wizard_text = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    domain_text = f"Domain: {domain.domain}, Product: {domain.product_name}"

    prompt = WIZARD_SYNTHESIS_PROMPT.format(wizard_answers=f"{domain_text}\n{wizard_text}")

    result = asyncio.run(
        llm.structured_complete(
            prompt,
            [{"role": "user", "content": "Generate the persona now."}],
            model_label,
            PersonaModel,
        )
    )
    return result  # type: ignore[return-value]


def _build_mechanical_persona(answers: dict[str, str], domain: DomainContext) -> PersonaModel:
    """Fallback: build persona from answers without LLM synthesis."""
    role = answers["role"]
    return PersonaModel(
        persona=f"{role.title()} User",
        role=role,
        archetype_label=f"The {role.title()}",
        version=1.0,
        last_refreshed=date.today(),
        changelog=[
            ChangelogEntry(date=date.today(), change="Initial creation via wizard (no LLM)")
        ],
        identity=IdentityAndMotivations(
            context=[answers.get("day_description", "")],
            jobs_to_be_done=[
                JobToBeDone(
                    title=answers.get("main_jobs", "Primary job"),
                    when="During their typical workflow",
                    i_want_to=answers.get("main_jobs", "accomplish their primary task"),
                    so_i_can=answers.get("success_failure", "succeed"),
                    functional_success="Task completed correctly",
                    emotional_success="Feeling confident",
                    social_success="Seen as competent",
                )
            ],
            fundamental_motivations=["Efficiency", "Reliability"],
        ),
        context=ContextAndConstraints(
            technology=TechnologyProfile(
                primary_device="Laptop",
                tech_comfort=answers.get("tech_savvy", "Moderate"),
                platform_stack=answers.get("competing_tools", "").split(","),
            ),
            channels=ChannelPreferences(preferred=["Email"], avoided=["None specified"]),
            trust=TrustPosture(
                toward_product="Neutral",
                toward_technology="Moderate adopter",
                specific_concerns=[],
            ),
        ),
        workflows=WorkflowsAndPainPoints(
            typical_arc=["Uses product during work hours"],
            pain_points=[
                PainPoint(
                    pain_point=answers.get("biggest_frustration", "Unspecified frustration"),
                    concrete_example="See wizard answers for details",
                    severity=3,
                    evidence="wizard-reported",
                )
            ],
            compensating_behaviors=[answers.get("workarounds", "None specified")],
            failure_modes=[answers.get("cascade_effects", "Downstream impact unknown")],
        ),
        evidence=EvidenceAndProvenance(
            thin_data_areas=[answers.get("unknown", "No gaps specified")],
            assumed_but_unverified=["Most wizard answers are self-reported"],
            representativeness_note=f"Confidence: {answers.get('confidence', 'unknown')}",
        ),
        simulation=SimulationControls(
            voice=VoiceAndTone(
                speaking_style="Direct",
                vocabulary_level="Industry standard",
                emotional_baseline="Neutral",
            ),
            hard_constraints=[
                "Push back when a proposal doesn't match your daily reality",
                "Express skepticism about solutions that add steps",
                "Do NOT agree just because the interviewer seems enthusiastic",
            ],
            abstention_rules=[
                "If a topic is in Known Gaps, vary your answer rather than inventing",
                "If asked about a product area you don't use, say so",
            ],
            anti_sycophancy_directives=[
                "When evaluating a solution, name at least one adoption barrier",
                "When asked 'would you use this?', consider whether you'd actually change behavior",
                "If something sounds too good to be true, say so",
            ],
        ),
    )


def run_persona_wizard(directory: Path = Path("personas")) -> None:
    """Run the full persona creation wizard."""
    store = PersonaStore(directory)

    console.print(
        Panel(
            "[bold]Persona Creation Wizard[/bold]\n\n"
            "This wizard interviews you about your product and users, then "
            "generates evidence-grounded personas with anti-sycophancy controls.",
            title="synth persona create",
        )
    )

    # Phase 1: Domain context
    domain = _collect_domain_context(store)

    # Phase 2: Per-role persona creation
    roles = domain.user_roles
    if not roles:
        roles = _ask_multi("Enter user roles to create personas for (comma-separated)")

    for role in roles:
        console.print(f"\n[bold]Creating persona for: {role}[/bold]")
        answers = _collect_persona_answers(role, domain)

        # Try LLM synthesis, fall back to mechanical
        try:
            config = AppConfig.load()
            if config.models:
                console.print("[dim]Synthesizing persona with LLM...[/dim]")
                persona = _synthesize_with_llm(answers, domain)
            else:
                raise RuntimeError("No models configured")
        except Exception as e:
            console.print(
                f"[yellow]LLM synthesis unavailable ({e}). Using mechanical template.[/yellow]\n"
                "[dim]Run `synth init` to configure an API key, then "
                "`synth persona research` to enrich.[/dim]"
            )
            persona = _build_mechanical_persona(answers, domain)

        # Phase 3: Archetype splitting
        if Confirm.ask(
            f"\nWithin '{role}', are there meaningfully different sub-types?",
            default=False,
        ):
            sub_types = _ask_multi("List the sub-types (comma-separated)")
            for sub in sub_types:
                console.print(f"\n[dim]Creating archetype: {sub}[/dim]")
                sub_persona = persona.model_copy(
                    update={
                        "sub_role": sub.lower().replace(" ", "_"),
                        "archetype_label": f"The {sub}",
                    }
                )
                slug = f"{role.lower()}-{sub.lower().replace(' ', '-')}"
                path = store.save(sub_persona, slug)
                console.print(f"[green]Saved: {path}[/green]")
        else:
            path = store.save(persona)
            console.print(f"[green]Saved: {path}[/green]")

    console.print(
        "\n[bold green]Persona creation complete![/bold green]\n"
        "Next: run `synth persona research <slug>` to enrich with web evidence."
    )
