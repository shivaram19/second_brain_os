"""Abstract base class for agents.

Defines the canonical contract for all Second Brain OS agents:
  async run(task: TaskSpec) -> AgentResult

Agents are autonomous workers that consume a task specification, use the
knowledge base and context engineering layers to gather relevant context,
optionally call an LLM, and return a structured result.

The abstraction allows the AgentOrchestrator to compose agents into workflows
(research → draft → publish) without knowing implementation details.
"""

from abc import ABC, abstractmethod

from brainos.core.models import AgentResult, TaskSpec


class AbstractAgent(ABC):
    """Base class for agentic task execution."""

    @abstractmethod
    async def run(self, task: TaskSpec) -> AgentResult:
        """Execute a task.

        Args:
            task: Task specification

        Returns:
            Result of task execution
        """
