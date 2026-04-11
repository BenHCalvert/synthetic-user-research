"""Tests for synthesis and panel output Pydantic models."""

from synth.models.synthesis import (
    AdvocateStatus,
    ChallengeReport,
    ConfidenceTag,
    Grounding,
    Hypothesis,
    ModelAgreement,
    PanelResult,
    SynthesisReport,
    TriageEntry,
)


class TestConfidenceTag:
    def test_all_grounding_levels(self):
        for g in Grounding:
            tag = ConfidenceTag(
                grounding=g,
                model_agreement=ModelAgreement.converged,
                advocate_status=AdvocateStatus.unchallenged,
            )
            assert tag.grounding == g

    def test_all_model_agreement_levels(self):
        for ma in ModelAgreement:
            tag = ConfidenceTag(
                grounding=Grounding.grounded,
                model_agreement=ma,
                advocate_status=AdvocateStatus.unchallenged,
            )
            assert tag.model_agreement == ma


class TestHypothesis:
    def test_valid_hypothesis(self):
        h = Hypothesis(
            statement="Users prefer inline editing over modal dialogs",
            confidence=ConfidenceTag(
                grounding=Grounding.plausible,
                model_agreement=ModelAgreement.converged,
                advocate_status=AdvocateStatus.unchallenged,
            ),
            priority="validate",
            validation_target="Power users who edit frequently",
        )
        assert h.priority == "validate"
        assert h.validation_target is not None

    def test_hypothesis_without_validation_target(self):
        h = Hypothesis(
            statement="Test statement",
            confidence=ConfidenceTag(
                grounding=Grounding.speculative,
                model_agreement=ModelAgreement.single_model,
                advocate_status=AdvocateStatus.challenged,
            ),
            priority="monitor",
        )
        assert h.validation_target is None


class TestSynthesisReport:
    def test_valid_report(self):
        report = SynthesisReport(
            themes=["Theme 1", "Theme 2"],
            surprises=["Surprise 1"],
            pushback_points=["Pushback 1"],
            questions_for_real_interviews=["Question 1"],
            hypotheses=[
                Hypothesis(
                    statement="Test",
                    confidence=ConfidenceTag(
                        grounding=Grounding.grounded,
                        model_agreement=ModelAgreement.converged,
                        advocate_status=AdvocateStatus.unchallenged,
                    ),
                    priority="accept",
                )
            ],
        )
        assert len(report.themes) == 2


class TestChallengeReport:
    def test_valid_challenge_report(self):
        report = ChallengeReport(
            sycophancy_checks=["Personas agreed too easily on feature X"],
            missing_objections=["No one mentioned learning curve"],
            ideal_user_assumptions=["Assumes users check notifications daily"],
            uncovered_edge_cases=["What about users with screen readers?"],
            challenged_themes=["Feature X adoption"],
        )
        assert len(report.challenged_themes) == 1


class TestPanelResult:
    def test_minimal_panel_result(self):
        result = PanelResult(
            topic="Test topic",
            date="2026-04-10",
            mode="problem-discovery",
            model_depth="standard",
            models_used=["Claude", "GPT-4o"],
            triage=[
                TriageEntry(
                    persona_slug="test-user",
                    persona_name="Test User",
                    model_label="Claude",
                    reaction="mixed",
                    summary="Some concerns about adoption",
                )
            ],
            convergent_themes=[],
            model_divergent_themes=[],
            persona_divergent_themes=[],
            blind_spots=[],
            advocate_addendum=ChallengeReport(
                sycophancy_checks=[],
                missing_objections=[],
                ideal_user_assumptions=[],
                uncovered_edge_cases=[],
                challenged_themes=[],
            ),
            hypotheses=[],
        )
        assert result.topic == "Test topic"
        assert len(result.models_used) == 2
