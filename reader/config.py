"""
Configuration loading for the reader module.
"""
from pathlib import Path
from typing import Any

import yaml

READER_DIR = Path(__file__).parent
REGISTRY_PATH = READER_DIR / "content_registry.yaml"
CONFIG_PATH = READER_DIR / "config.yaml"


def load_registry() -> dict[str, Any]:
    """Load the content registry."""
    if not REGISTRY_PATH.exists():
        return {"materials": {}}

    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f) or {"materials": {}}


def load_config() -> dict[str, Any]:
    """Load reader configuration (API keys, etc.)."""
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def get_material(material_id: str) -> dict[str, Any]:
    """Get a specific material's configuration."""
    registry = load_registry()
    materials = registry.get("materials", {})

    if material_id not in materials:
        raise ValueError(f"Material '{material_id}' not found in registry")

    return materials[material_id]
