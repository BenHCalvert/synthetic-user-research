"""Persona store: read/write/list persona YAML files with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from synth.models.persona import DomainContext, PersonaModel

console = Console()


def _slug_from_persona(persona: PersonaModel) -> str:
    """Generate a filesystem slug from a persona name."""
    return persona.persona.lower().replace(" ", "-").replace("'", "").replace('"', "")


class PersonaStore:
    """Read, write, list, and validate persona YAML files."""

    def __init__(self, directory: Path = Path("personas")):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, persona: PersonaModel, slug: str | None = None) -> Path:
        """Serialize a PersonaModel to YAML and write to disk."""
        if slug is None:
            slug = _slug_from_persona(persona)
        path = self.directory / f"{slug}.yaml"
        data = persona.model_dump(mode="json")
        path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return path

    def load(self, slug: str) -> PersonaModel | None:
        """Load and validate a persona from YAML."""
        path = self.directory / f"{slug}.yaml"
        if not path.exists():
            return None
        with open(path) as f:
            data = yaml.safe_load(f)
        return PersonaModel(**data)

    def list_all(self) -> dict[str, PersonaModel]:
        """List all valid personas in the directory."""
        personas: dict[str, PersonaModel] = {}
        for path in sorted(self.directory.glob("*.yaml")):
            if path.name.startswith("."):
                continue
            slug = path.stem
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                personas[slug] = PersonaModel(**data)
            except Exception as e:
                console.print(f"[yellow]Warning: skipping {path.name}: {e}[/yellow]")
        return personas

    def load_domain_context(self) -> DomainContext | None:
        """Load shared domain context from .domain.yaml."""
        path = self.directory / ".domain.yaml"
        if not path.exists():
            return None
        with open(path) as f:
            data = yaml.safe_load(f)
        return DomainContext(**data)

    def save_domain_context(self, ctx: DomainContext) -> Path:
        """Save shared domain context."""
        path = self.directory / ".domain.yaml"
        data = ctx.model_dump(mode="json")
        path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return path

    def load_presets(self) -> dict[str, Any]:
        """Load panel presets from .panels.yaml."""
        path = self.directory / ".panels.yaml"
        if not path.exists():
            return {}
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return data.get("presets", {})
