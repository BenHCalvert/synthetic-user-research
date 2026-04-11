"""Structural validation tests for PersonaModel and related schemas."""

from datetime import date

import pytest
from pydantic import ValidationError

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
    RefreshSource,
    SimulationControls,
    TechnologyProfile,
    TrustPosture,
    VoiceAndTone,
    WorkflowsAndPainPoints,
)


def _make_minimal_persona(**overrides) -> PersonaModel:
    """Create a minimal valid persona for testing."""
    defaults = dict(
        persona="Test User",
        role="tester",
        archetype_label="The Tester",
        identity=IdentityAndMotivations(
            context=["A QA engineer at a mid-size SaaS company"],
            jobs_to_be_done=[
                JobToBeDone(
                    title="Verify releases",
                    when="Before each deployment",
                    i_want_to="run the full test suite",
                    so_i_can="catch regressions before users do",
                    functional_success="All tests pass, coverage above threshold",
                    emotional_success="Confident the release is solid",
                    social_success="Team trusts the release process",
                )
            ],
            fundamental_motivations=[
                "Values thoroughness over speed",
                "Driven by preventing user-facing bugs",
            ],
        ),
        context=ContextAndConstraints(
            technology=TechnologyProfile(
                primary_device="Laptop",
                tech_comfort="Can write scripts, comfortable with CLI tools",
                platform_stack=["Jira", "GitHub", "Selenium", "Slack"],
            ),
            channels=ChannelPreferences(
                preferred=["Slack", "Jira comments"],
                avoided=["Email threads"],
            ),
            trust=TrustPosture(
                toward_product="Skeptical -- has been burned by flaky tests",
                toward_technology="Early adopter for testing tools",
                specific_concerns=["Test flakiness", "CI pipeline reliability"],
            ),
        ),
        workflows=WorkflowsAndPainPoints(
            typical_arc=["Checks CI dashboard first thing, triages failures by 10am"],
            pain_points=[
                PainPoint(
                    pain_point="Flaky tests waste hours of investigation",
                    concrete_example=(
                        "Spent 3 hours last week on a test that failed "
                        "due to timing, not a real bug"
                    ),
                    severity=4,
                    evidence="wizard-reported",
                )
            ],
            compensating_behaviors=["Maintains a spreadsheet of known-flaky tests"],
            failure_modes=[
                "When CI is red for hours, developers stop trusting it and merge without checks"
            ],
        ),
        evidence=EvidenceAndProvenance(
            thin_data_areas=["Don't know how they handle mobile testing"],
        ),
        simulation=SimulationControls(
            voice=VoiceAndTone(
                speaking_style="Direct and technical",
                vocabulary_level="Uses CI/CD terminology freely",
                emotional_baseline="Mildly frustrated but persistent",
            ),
            hard_constraints=[
                "Push back on anything that adds manual steps to the release process",
                "Won't trust a tool that can't integrate with GitHub Actions",
            ],
            abstention_rules=[
                "If asked about frontend testing, say 'that's not my area'",
            ],
            anti_sycophancy_directives=[
                "When shown a new testing tool, ask 'does it handle flaky test detection?'",
                "If it sounds too easy, say 'I've heard that before about other tools'",
            ],
        ),
    )
    defaults.update(overrides)
    return PersonaModel(**defaults)


class TestPersonaModel:
    def test_minimal_valid_persona(self):
        persona = _make_minimal_persona()
        assert persona.persona == "Test User"
        assert persona.role == "tester"
        assert persona.version == 1.0

    def test_default_last_refreshed_is_today(self):
        persona = _make_minimal_persona()
        assert persona.last_refreshed == date.today()

    def test_default_staleness_threshold(self):
        persona = _make_minimal_persona()
        assert persona.staleness_threshold_days == 90

    def test_jtbd_requires_at_least_one(self):
        with pytest.raises(ValidationError):
            _make_minimal_persona(
                identity=IdentityAndMotivations(
                    context=["test"],
                    jobs_to_be_done=[],
                    fundamental_motivations=["a", "b"],
                )
            )

    def test_motivations_require_at_least_two(self):
        with pytest.raises(ValidationError):
            _make_minimal_persona(
                identity=IdentityAndMotivations(
                    context=["test"],
                    jobs_to_be_done=[
                        JobToBeDone(
                            title="t",
                            when="w",
                            i_want_to="i",
                            so_i_can="s",
                            functional_success="f",
                            emotional_success="e",
                            social_success="s",
                        )
                    ],
                    fundamental_motivations=["only one"],
                )
            )

    def test_pain_point_severity_range(self):
        with pytest.raises(ValidationError):
            PainPoint(
                pain_point="test",
                concrete_example="test",
                severity=6,
                evidence="test",
            )

    def test_pain_point_severity_min(self):
        with pytest.raises(ValidationError):
            PainPoint(
                pain_point="test",
                concrete_example="test",
                severity=0,
                evidence="test",
            )

    def test_hard_constraints_required(self):
        with pytest.raises(ValidationError):
            SimulationControls(
                voice=VoiceAndTone(
                    speaking_style="a", vocabulary_level="b", emotional_baseline="c"
                ),
                hard_constraints=[],
                abstention_rules=["x"],
                anti_sycophancy_directives=["y"],
            )

    def test_serialization_roundtrip(self):
        persona = _make_minimal_persona()
        data = persona.model_dump(mode="json")
        restored = PersonaModel(**data)
        assert restored.persona == persona.persona
        assert len(restored.identity.jobs_to_be_done) == len(persona.identity.jobs_to_be_done)
        assert (
            restored.workflows.pain_points[0].severity == persona.workflows.pain_points[0].severity
        )

    def test_changelog_and_refresh_sources(self):
        persona = _make_minimal_persona(
            changelog=[ChangelogEntry(date=date.today(), change="Created")],
            refresh_sources=[RefreshSource(source="Reddit", date=date.today(), scope="r/testing")],
        )
        assert len(persona.changelog) == 1
        assert len(persona.refresh_sources) == 1


class TestDomainContext:
    def test_minimal_domain_context(self):
        ctx = DomainContext(domain="Project Management SaaS")
        assert ctx.domain == "Project Management SaaS"
        assert ctx.user_roles == []

    def test_full_domain_context(self):
        ctx = DomainContext(
            domain="K-12 Education",
            product_name="SchoolApp",
            user_roles=["teacher", "parent", "admin"],
            key_frustrations=["Too many notifications", "Confusing permissions"],
            research_sources={
                "subreddits": ["r/Teachers", "r/education"],
                "app_store_id": "com.school.app",
            },
        )
        assert len(ctx.user_roles) == 3
        assert "subreddits" in ctx.research_sources
