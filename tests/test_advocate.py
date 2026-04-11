"""Tests for the devil's advocate engine."""

from synth.core.advocate import apply_advocate_challenges
from synth.models.synthesis import (
    AdvocateStatus,
    ChallengeReport,
    ConfidenceTag,
    Grounding,
    Hypothesis,
    ModelAgreement,
)


class TestApplyAdvocateChallenges:
    def test_unchallenged_hypothesis_stays_unchallenged(self):
        hypotheses = [
            Hypothesis(
                statement="Users want inline editing",
                confidence=ConfidenceTag(
                    grounding=Grounding.grounded,
                    model_agreement=ModelAgreement.converged,
                    advocate_status=AdvocateStatus.unchallenged,
                ),
                priority="accept",
            )
        ]
        report = ChallengeReport(
            sycophancy_checks=[],
            missing_objections=[],
            ideal_user_assumptions=[],
            uncovered_edge_cases=[],
            challenged_themes=["different theme"],
        )
        result = apply_advocate_challenges(hypotheses, report)
        assert result[0].confidence.advocate_status == AdvocateStatus.unchallenged

    def test_challenged_hypothesis_gets_updated(self):
        hypotheses = [
            Hypothesis(
                statement="Users want inline editing",
                confidence=ConfidenceTag(
                    grounding=Grounding.plausible,
                    model_agreement=ModelAgreement.converged,
                    advocate_status=AdvocateStatus.unchallenged,
                ),
                priority="accept",
            )
        ]
        report = ChallengeReport(
            sycophancy_checks=["Too much agreement on inline editing"],
            missing_objections=[],
            ideal_user_assumptions=[],
            uncovered_edge_cases=[],
            challenged_themes=["inline editing"],
        )
        result = apply_advocate_challenges(hypotheses, report)
        assert result[0].confidence.advocate_status == AdvocateStatus.challenged

    def test_preserves_other_confidence_fields(self):
        hypotheses = [
            Hypothesis(
                statement="Users want inline editing",
                confidence=ConfidenceTag(
                    grounding=Grounding.speculative,
                    model_agreement=ModelAgreement.diverged,
                    advocate_status=AdvocateStatus.unchallenged,
                ),
                priority="validate",
            )
        ]
        report = ChallengeReport(
            sycophancy_checks=[],
            missing_objections=[],
            ideal_user_assumptions=[],
            uncovered_edge_cases=[],
            challenged_themes=["inline editing"],
        )
        result = apply_advocate_challenges(hypotheses, report)
        assert result[0].confidence.grounding == Grounding.speculative
        assert result[0].confidence.model_agreement == ModelAgreement.diverged
        assert result[0].priority == "validate"
