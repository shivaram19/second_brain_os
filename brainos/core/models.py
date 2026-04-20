"""Domain models for Second Brain OS.

Defines the canonical data structures for the knowledge system:
  - Idea: A markdown note from the Obsidian vault with frontmatter metadata
  - Chunk: A text segment from an Idea, ready for embedding
  - GraphNode / GraphEdge: Nodes and relationships in the knowledge graph
  - TaskSpec / AgentResult: Agent task execution types
  - PersonaBlock: The instruction layer (values, tone, decision framework)
  - ContextSlice: A scored piece of context from one of the three layers
  - RetrievedFacts: Results from hybrid retrieval (semantic + graph)
  - BudgetSpec: Token budget for context packing

All models extend Pydantic BaseModel for runtime validation, JSON serialization,
and automatic schema generation (required for MCP tool/resource definitions).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class NodeType(str, Enum):
    """Type of graph node."""
    IDEA = "idea"
    TOPIC = "topic"
    PROJECT = "project"
    PERSON = "person"
    PRINCIPLE = "principle"
    CONCEPT = "concept"


class EdgeType(str, Enum):
    """Type of relationship between graph nodes."""
    LINKS_TO = "links_to"
    RELATES_TO = "relates_to"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    BELONGS_TO = "belongs_to"
    EXTENDS = "extends"
    INSPIRED_BY = "inspired_by"


class ContextLayer(str, Enum):
    """Context stack layer."""
    INSTRUCTION = "instruction"
    KNOWLEDGE = "knowledge"
    TOOLS = "tools"


class Idea(BaseModel):
    """A note/idea in the Obsidian vault."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    vault_path: str  # relative path from vault root

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Systems Thinking",
                "content": "A holistic approach to understanding complex systems...",
                "frontmatter": {"status": "active", "domain": "philosophy"},
                "tags": ["thinking", "philosophy"],
                "vault_path": "concepts/systems-thinking.md",
            }
        }


class Chunk(BaseModel):
    """A text chunk from an Idea, ready for embedding."""
    id: UUID = Field(default_factory=uuid4)
    idea_id: UUID
    text: str
    chunk_index: int = 0
    token_count: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Systems thinking involves understanding...",
                "chunk_index": 0,
                "token_count": 42,
            }
        }


class GraphNode(BaseModel):
    """A node in the knowledge graph."""
    node_id: str  # typically the Idea.id or note filename
    label: str
    node_type: NodeType = NodeType.IDEA
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "systems-thinking",
                "label": "Systems Thinking",
                "node_type": "concept",
                "properties": {"importance": 8},
            }
        }


class GraphEdge(BaseModel):
    """An edge (relationship) in the knowledge graph."""
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.RELATES_TO
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "systems-thinking",
                "target_id": "complexity",
                "edge_type": "relates_to",
                "weight": 0.85,
            }
        }


class TaskSpec(BaseModel):
    """A task to be executed by an agent."""
    id: UUID = Field(default_factory=uuid4)
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5  # 1-10 scale
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    linked_ideas: List[UUID] = Field(default_factory=list)


class PersonaBlock(BaseModel):
    """Instruction layer: persona, values, and decision framework."""
    name: str
    values: List[str]
    tone: str
    reasoning_style: str
    decision_framework: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Systems Architect",
                "values": ["Systems Thinking", "Effective Altruism", "Intellectual Honesty"],
                "tone": "clear, precise, thoughtful",
                "reasoning_style": "first-principles, evidence-based",
                "decision_framework": "impact x neglectedness x solvability",
            }
        }


class ContextSlice(BaseModel):
    """A single piece of context from one of the three layers."""
    layer: ContextLayer
    content: str
    token_count: int
    source: str  # which note, which tool, etc.
    relevance_score: float = 0.5


class RetrievedFacts(BaseModel):
    """Results from hybrid retrieval (semantic + graph)."""
    query: str
    semantic_results: List[Chunk] = Field(default_factory=list)
    graph_results: List[GraphNode] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def total_results(self) -> int:
        return len(self.semantic_results) + len(self.graph_results)


class BudgetSpec(BaseModel):
    """Token budget for context packing."""
    total_tokens: int = 100000
    instruction_budget: int = 15000
    knowledge_budget: int = 70000
    tool_budget: int = 15000

    def validate(self) -> bool:
        """Ensure budgets don't exceed total."""
        return (
            self.instruction_budget + self.knowledge_budget + self.tool_budget
            <= self.total_tokens
        )


class AgentResult(BaseModel):
    """Result from running an agent."""
    task_id: UUID
    status: TaskStatus
    output: str
    context_used: List[ContextSlice] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
