"""Evidence traceability spot-checks for persona schemas."""

import yaml

from synth.models.persona import PersonaModel


class TestEvidenceTraceability:
    """Verify that persona pain points and claims cite evidence sources."""

    def test_pain_points_have_evidence(self):
        """Every pain point must have a non-empty evidence field."""
        from tests.test_persona_schema import _make_minimal_persona

        persona = _make_minimal_persona()
        for pp in persona.workflows.pain_points:
            assert pp.evidence, f"Pain point '{pp.pain_point}' has no evidence citation"

    def test_thin_data_areas_declared(self):
        """Persona must declare at least one thin data area."""
        from tests.test_persona_schema import _make_minimal_persona

        persona = _make_minimal_persona()
        assert len(persona.evidence.thin_data_areas) > 0, "Persona must declare known gaps"

    def test_anti_sycophancy_directives_are_specific(self):
        """Anti-sycophancy directives should reference persona-specific details."""
        from tests.test_persona_schema import _make_minimal_persona

        persona = _make_minimal_persona()
        for directive in persona.simulation.anti_sycophancy_directives:
            # Directives should be longer than a generic statement
            assert len(directive) > 20, f"Directive too generic: '{directive}'"

    def test_yaml_roundtrip_preserves_evidence(self):
        """Serializing to YAML and back should preserve evidence fields."""
        from tests.test_persona_schema import _make_minimal_persona

        persona = _make_minimal_persona()
        yaml_str = yaml.dump(persona.model_dump(mode="json"), default_flow_style=False)
        restored_data = yaml.safe_load(yaml_str)
        restored = PersonaModel(**restored_data)

        assert restored.evidence.thin_data_areas == persona.evidence.thin_data_areas
        assert len(restored.workflows.pain_points) == len(persona.workflows.pain_points)
        for original, restored_pp in zip(
            persona.workflows.pain_points, restored.workflows.pain_points, strict=False
        ):
            assert restored_pp.evidence == original.evidence
