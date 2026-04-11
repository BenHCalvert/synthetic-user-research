"""LLM layer: litellm + instructor wrapper for multi-model dispatch."""

import asyncio

import instructor
import litellm
from pydantic import BaseModel

from synth.models.config import AppConfig, ModelConfig


class LLM:
    """Thin wrapper around litellm + instructor for multi-model dispatch."""

    def __init__(self, models: list[ModelConfig] | None = None):
        if models is None:
            config = AppConfig.load()
            models = config.models
        self.models = {m.label: m.model_id for m in models}
        self.client = instructor.from_litellm(litellm.acompletion)

    @property
    def available_labels(self) -> list[str]:
        return list(self.models.keys())

    async def complete(self, system: str, messages: list[dict[str, str]], model_label: str) -> str:
        """Free-text completion. Used for conversational interviews."""
        response = await litellm.acompletion(
            model=self.models[model_label],
            messages=[{"role": "system", "content": system}, *messages],
        )
        return response.choices[0].message.content  # type: ignore[return-value]

    async def structured_complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        model_label: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Structured output via instructor. Returns a validated Pydantic model."""
        return await self.client.chat.completions.create(
            model=self.models[model_label],
            messages=[{"role": "system", "content": system}, *messages],  # type: ignore[arg-type]
            response_model=response_model,
        )

    async def parallel_complete(
        self, system: str, messages: list[dict[str, str]], model_labels: list[str]
    ) -> dict[str, str]:
        """Run the same prompt across multiple models in parallel."""
        tasks = {label: self.complete(system, messages, label) for label in model_labels}
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results, strict=False))

    async def parallel_structured(
        self,
        system: str,
        messages: list[dict[str, str]],
        model_labels: list[str],
        response_model: type[BaseModel],
    ) -> dict[str, BaseModel]:
        """Structured output across multiple models in parallel."""
        tasks = {
            label: self.structured_complete(system, messages, label, response_model)
            for label in model_labels
        }
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results, strict=False))
