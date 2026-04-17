"""Tests for synth init command logic."""

from synth.commands.init import _model_provider, _print_key_status
from synth.models.config import ModelConfig, WebSearchConfig


class TestModelProvider:
    def test_anthropic_prefixed(self):
        assert _model_provider("anthropic/claude-sonnet-4-20250514") == "anthropic"

    def test_claude_shorthand(self):
        assert _model_provider("claude-3-5-sonnet") == "anthropic"

    def test_gpt_prefix(self):
        assert _model_provider("gpt-4o") == "openai"

    def test_openai_prefix(self):
        assert _model_provider("openai/gpt-4o-mini") == "openai"

    def test_o1_series(self):
        assert _model_provider("o1-preview") == "openai"

    def test_gemini_prefix(self):
        assert _model_provider("gemini/gemini-2.5-pro") == "google"

    def test_gemini_shorthand(self):
        assert _model_provider("gemini-2.0-flash") == "google"

    def test_unknown_returns_empty(self):
        assert _model_provider("some-unknown-model") == ""


class TestPrintKeyStatus:
    def test_returns_missing_keys_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        models = [
            ModelConfig(model_id="anthropic/claude-sonnet-4-20250514", label="Claude"),
            ModelConfig(model_id="gpt-4o", label="GPT-4o"),
        ]
        missing = _print_key_status(models, WebSearchConfig(provider="tavily"))
        assert "ANTHROPIC_API_KEY" in missing
        assert "OPENAI_API_KEY" in missing

    def test_returns_empty_when_all_keys_set(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

        models = [ModelConfig(model_id="anthropic/claude-sonnet-4-20250514", label="Claude")]
        missing = _print_key_status(models, WebSearchConfig(provider="tavily"))
        assert missing == []

    def test_search_key_included(self, monkeypatch):
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        models = [ModelConfig(model_id="anthropic/claude-sonnet-4-20250514", label="Claude")]
        missing = _print_key_status(models, WebSearchConfig(provider="brave"))
        assert "BRAVE_API_KEY" in missing
        assert "ANTHROPIC_API_KEY" not in missing

    def test_unknown_model_provider_skipped(self, monkeypatch):
        """Models with unrecognised providers don't crash or emit spurious missing keys."""
        models = [ModelConfig(model_id="some-custom-model", label="Custom")]
        missing = _print_key_status(models, WebSearchConfig(provider="tavily"))
        assert "SOME_CUSTOM_MODEL_API_KEY" not in missing
