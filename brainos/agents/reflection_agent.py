"""Reflection agent for introspection and self-understanding.

The ReflectionAgent analyzes the user's knowledge graph and query history
to generate insights about their thinking:
  - Core Concepts: Most connected ideas (foundation of thinking)
  - Blindspots: Isolated concepts that need linking
  - Suggested Connections: Pairs of unlinked concepts with shared neighbors
  - Thinking Patterns: Frequent queries and keywords from telemetry
  - Knowledge Summary: Graph stats (nodes, edges, density, centrality)

It uses ReflectionAnalyzer for graph analytics and formats results into
human-readable markdown reports. Can be run on-demand or as part of a
daily workflow.
"""

import json
from typing import Any, Dict

from brainos.agents.reflection_analyzer import ReflectionAnalyzer
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.telemetry.schema import TelemetryDB


class ReflectionAgent:
    """Agent that reflects on your knowledge and generates insights."""

    def __init__(self, vault_path: str, telemetry_db_path: str):
        """Initialize reflection agent.

        Args:
            vault_path: Path to Obsidian vault
            telemetry_db_path: Path to telemetry database
        """
        self.vault_adapter = VaultAdapter(vault_path)
        self.telemetry = TelemetryDB(telemetry_db_path)
        self.graph_builder = GraphBuilder()

        # Load ideas and build graph
        self.ideas = self.vault_adapter.ingest_all()
        self.graph_builder.build_from_ideas(self.ideas)

        self.analyzer = ReflectionAnalyzer(
            self.graph_builder, self.ideas, self.telemetry
        )

    def reflect_core_concepts(self) -> str:
        """Reflect on core concepts."""
        concepts = self.analyzer.get_core_concepts(top_k=5)

        text = "🧠 Your Core Concepts\n\n"
        text += "These are the ideas you think about most:\n\n"

        for i, (name, connections) in enumerate(concepts, 1):
            text += f"{i}. **{name}** ({connections} connections)\n"

        text += "\n💡 Insight: These form the foundation of your thinking.\n"
        return text

    def reflect_blindspots(self) -> str:
        """Reflect on knowledge gaps."""
        blindspots = self.analyzer.get_blindspots()

        if not blindspots:
            return "✅ Your concepts are well-connected! No obvious blindspots.\n"

        text = "⚠️ Knowledge Blindspots\n\n"
        text += "These concepts are isolated (not connected to much):\n\n"

        for i, name in enumerate(blindspots[:5], 1):
            text += f"{i}. {name}\n"

        text += (
            "\n💭 Consider: How do these relate to your core concepts?\n"
            "Connecting them could deepen your understanding.\n"
        )
        return text

    def reflect_suggested_connections(self) -> str:
        """Suggest connections to explore."""
        suggestions = self.analyzer.get_suggestion_connections(top_k=5)

        if not suggestions:
            return "Your knowledge is well-connected!\n"

        text = "🔗 Suggested Connections to Explore\n\n"
        text += "Based on shared relationships, consider connecting:\n\n"

        for i, sugg in enumerate(suggestions, 1):
            text += (
                f"{i}. **{sugg['source']}** ↔ **{sugg['target']}**\n"
                f"   {sugg['reason']}\n\n"
            )

        return text

    def reflect_thinking_patterns(self) -> str:
        """Reflect on thinking patterns."""
        patterns = self.analyzer.get_thinking_patterns()

        text = "🎯 Your Thinking Patterns\n\n"

        if patterns["top_queries"]:
            text += "Most frequent questions:\n"
            for i, query in enumerate(patterns["top_queries"][:3], 1):
                text += f"{i}. \"{query['query']}\" (asked {query['count']} times)\n"
            text += "\n"

        if patterns["top_keywords"]:
            text += "You often think about: " + ", ".join(patterns["top_keywords"]) + "\n\n"

        text += f"Total queries: {patterns['total_queries']}\n"
        return text

    def reflect_summary(self) -> str:
        """Get high-level summary."""
        summary = self.analyzer.get_knowledge_summary()

        text = "📊 Knowledge Summary\n\n"
        text += f"• **Concepts**: {summary['total_concepts']}\n"
        text += f"• **Connections**: {summary['total_connections']}\n"
        text += f"• **Avg connections per concept**: {summary['avg_connections_per_concept']:.1f}\n"
        text += f"• **Graph density**: {summary['graph_density']:.2%}\n"
        text += f"• **Most important concept**: {summary['most_connected']}\n\n"

        density_interpretation = (
            "Your knowledge is highly integrated"
            if summary["graph_density"] > 0.3
            else "Your knowledge has distinct clusters"
        )
        text += f"💡 {density_interpretation}.\n"

        return text

    def reflect_full(self) -> str:
        """Generate full reflection report."""
        full_reflection = self.analyzer.get_full_reflection()

        text = "═" * 60 + "\n"
        text += "         📖 KNOWLEDGE REFLECTION REPORT\n"
        text += "═" * 60 + "\n\n"

        # Summary
        text += self.reflect_summary()
        text += "\n" + "─" * 60 + "\n\n"

        # Core concepts
        text += self.reflect_core_concepts()
        text += "\n" + "─" * 60 + "\n\n"

        # Blindspots
        text += self.reflect_blindspots()
        text += "\n" + "─" * 60 + "\n\n"

        # Suggested connections
        text += self.reflect_suggested_connections()
        text += "\n" + "─" * 60 + "\n\n"

        # Thinking patterns
        text += self.reflect_thinking_patterns()
        text += "\n" + "═" * 60 + "\n"

        return text

    def get_reflection_json(self) -> Dict[str, Any]:
        """Get reflection as structured JSON.

        Returns:
            Full reflection data
        """
        return self.analyzer.get_full_reflection()
