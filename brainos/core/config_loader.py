"""Configuration loading from YAML files.

Loads and validates the four canonical configuration files in config/:
  - persona.yaml: Instruction layer (values, tone, reasoning style)
  - goals.yaml: Time-horizon goals (annual, quarterly, weekly)
  - routing.yaml: Agent routing rules by idea type and platform
  - paths.yaml: File system paths (vault, indexes, telemetry DB)

The Config object is a Pydantic BaseModel that validates on load, ensuring
runtime consistency across the system. This enables human-readable, versionable
configuration without code changes.
"""

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, ValidationError


class Config(BaseModel):
    """Main configuration object."""
    persona: Dict[str, Any]
    goals: Dict[str, Any]
    routing: Dict[str, Any]
    paths: Dict[str, Any]

    class Config:
        extra = "allow"


def load_config(config_dir: Path = None) -> Config:
    """Load configuration from YAML files in config/ directory.

    Args:
        config_dir: Path to config directory. Defaults to ./config

    Returns:
        Validated Config object
    """
    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent / "config"

    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    config_data: Dict[str, Any] = {}

    # Load each YAML file
    for yaml_file in ["persona.yaml", "goals.yaml", "routing.yaml", "paths.yaml"]:
        file_path = config_dir / yaml_file
        if file_path.exists():
            with open(file_path, "r") as f:
                data = yaml.safe_load(f) or {}
                key = yaml_file.replace(".yaml", "")
                config_data[key] = data
        else:
            config_data[yaml_file.replace(".yaml", "")] = {}

    try:
        return Config(**config_data)
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")
