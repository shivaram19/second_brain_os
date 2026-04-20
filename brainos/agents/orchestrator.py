"""Agent Orchestrator - Routes tasks to appropriate agents.

AgentOrchestrator is the workflow composer for Second Brain OS. It maintains
instances of all agents and exposes high-level operations:
  - research(topic): Single-shot research
  - draft(topic): Single-shot drafting
  - research_and_draft(topic): Compose research insights into a draft
  - research_draft_and_publish(topic): Full pipeline to exported file
  - reflect_on_knowledge(): Run reflection and return insights
  - daily_workflow(): Reflect, export, and plan next explorations

It also handles telemetry logging for multi-step workflows and lazy-loads
the ReflectionAgent to avoid expensive graph construction when not needed.
"""

from typing import Any, Dict

from brainos.agents.drafting_agent import DraftingAgent
from brainos.agents.publishing_agent import PublishingAgent
from brainos.agents.reflection_agent import ReflectionAgent
from brainos.agents.research_agent import ResearchAgent
from brainos.core import load_config
from brainos.telemetry.schema import TelemetryDB


class AgentOrchestrator:
    """Orchestrates multiple agents for complex workflows."""

    def __init__(self):
        """Initialize orchestrator with all agents."""
        self.config = load_config()
        self.telemetry = TelemetryDB(
            self.config.paths.get("telemetry_db", "./.brainos/telemetry.db")
        )

        # Initialize agents
        self.research_agent = ResearchAgent()
        self.drafting_agent = DraftingAgent()
        self.publishing_agent = PublishingAgent()
        self.reflection_agent = None  # Lazy-load

    def _get_reflection_agent(self):
        """Lazy-load reflection agent."""
        if self.reflection_agent is None:
            vault_path = self.config.paths.get("obsidian_vault", "~/ObsidianVault")
            telemetry_db_path = self.config.paths.get("telemetry_db", "./.brainos/telemetry.db")
            self.reflection_agent = ReflectionAgent(vault_path, telemetry_db_path)
        return self.reflection_agent

    def research(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        """Run research workflow.

        Args:
            topic: Topic to research
            depth: "shallow", "medium", or "deep"

        Returns:
            Research results
        """
        return self.research_agent.research(topic, depth)

    def draft(
        self, topic: str, format_type: str = "essay", length: str = "medium"
    ) -> Dict[str, Any]:
        """Run drafting workflow.

        Args:
            topic: Topic to write about
            format_type: Type of content
            length: Length of content

        Returns:
            Drafted content
        """
        return self.drafting_agent.draft(topic, format_type, length)

    def research_and_draft(
        self, topic: str, format_type: str = "essay"
    ) -> Dict[str, Any]:
        """Research a topic, then draft content about it.

        Args:
            topic: Topic to research and write about
            format_type: Type of content to draft

        Returns:
            Dict with research and draft results
        """
        # Research
        research_result = self.research(topic, depth="medium")

        if research_result["status"] != "success":
            return research_result

        # Extract research insights to inform drafting
        research_insights = research_result["output"]

        # Draft (the drafting agent will use vault context)
        draft_result = self.drafting_agent.draft(topic, format_type, length="medium")

        if draft_result["status"] != "success":
            return draft_result

        # Combine results
        combined = {
            "status": "success",
            "topic": topic,
            "research_insights": research_insights,
            "draft": draft_result["output"],
            "format": format_type,
            "tokens_used": research_result["tokens_used"] + draft_result["tokens_used"],
        }

        self.telemetry.log_event(
            "research_and_draft",
            query=topic,
            tokens_used=combined["tokens_used"],
            metadata={"format": format_type},
        )

        return combined

    def research_draft_and_publish(
        self, topic: str, format_type: str = "essay", publish_format: str = "markdown"
    ) -> Dict[str, Any]:
        """Full workflow: research, draft, and publish.

        Args:
            topic: Topic to process
            format_type: Type of content to draft
            publish_format: Format to publish in

        Returns:
            Dict with full workflow results
        """
        # Research and draft
        rnd_result = self.research_and_draft(topic, format_type)

        if rnd_result["status"] != "success":
            return rnd_result

        # Publish the draft
        pub_result = self.publishing_agent.publish(
            content=rnd_result["draft"],
            title=f"{topic} - {format_type}",
            format_type=publish_format,
        )

        if pub_result["status"] != "success":
            return pub_result

        # Combine all results
        combined = {
            "status": "success",
            "topic": topic,
            "workflow": "research_draft_publish",
            "research": rnd_result["research_insights"],
            "draft": rnd_result["draft"],
            "published": pub_result["filepath"],
            "tokens_used": rnd_result["tokens_used"],
        }

        self.telemetry.log_event(
            "research_draft_publish",
            query=topic,
            tokens_used=combined["tokens_used"],
        )

        return combined

    def reflect_on_knowledge(self) -> Dict[str, Any]:
        """Reflect on your knowledge base.

        Returns:
            Reflection results
        """
        reflection_agent = self._get_reflection_agent()
        reflection = reflection_agent.reflect_full()

        self.telemetry.log_event("reflect_workflow")

        return {
            "status": "success",
            "reflection": reflection,
        }

    def daily_workflow(self) -> Dict[str, Any]:
        """Run daily workflow: reflect, identify insights, plan next topics.

        Returns:
            Daily workflow results
        """
        # 1. Reflect on knowledge
        reflection = self._get_reflection_agent()
        reflection_data = reflection.get_full_reflection()

        # 2. Export reflection
        pub_result = self.publishing_agent.export_reflection(reflection_data)

        # 3. Log workflow
        self.telemetry.log_event("daily_workflow")

        return {
            "status": "success",
            "workflow": "daily",
            "reflection_exported": pub_result["status"] == "success",
            "reflection_file": pub_result.get("filepath", ""),
            "core_concepts": [c[0] for c in reflection_data.get("core_concepts", [])[:5]],
            "suggested_explorations": [
                sugg["source"] for sugg in reflection_data.get("suggested_connections", [])[:3]
            ],
        }
