"""Core layer: Pydantic domain models and YAML configuration loading.

This module defines the foundational data structures used across all layers of
Second Brain OS. All entities (Idea, Chunk, GraphNode, TaskSpec, etc.) are
Pydantic BaseModels for validation, JSON serialization, and MCP schema generation.

The Config loader reads human-editable YAML from config/ and validates it on load,
enabling tuning without code changes.
"""

from .models import (
    Idea,
    Chunk,
    GraphNode,
    GraphEdge,
    TaskSpec,
    PersonaBlock,
    ContextSlice,
    RetrievedFacts,
    BudgetSpec,
    AgentResult,
)
from .config_loader import Config, load_config
from .moonshot_client import MoonshotClient, get_moonshot_client

__all__ = [
    "Idea",
    "Chunk",
    "GraphNode",
    "GraphEdge",
    "TaskSpec",
    "PersonaBlock",
    "ContextSlice",
    "RetrievedFacts",
    "BudgetSpec",
    "AgentResult",
    "Config",
    "load_config",
    "MoonshotClient",
    "get_moonshot_client",
]
