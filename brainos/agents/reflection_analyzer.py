"""Analyze knowledge graphs for self-insight and reflection.

ReflectionAnalyzer is the analytics engine behind ReflectionAgent. It operates
on the NetworkX knowledge graph and SQLite telemetry database to compute:
  - Core concepts: Nodes with highest combined in-degree + out-degree
  - Blindspots: Nodes with very few connections (isolated ideas)
  - Suggested connections: Unlinked node pairs sharing ≥2 neighbors
  - Thinking patterns: Query frequency analysis from telemetry
  - Knowledge summary: Overall graph topology metrics

These analytics help users understand the shape of their knowledge,
identify gaps, and discover unexpected relationships.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import networkx as nx

from brainos.core.models import Idea
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.telemetry.schema import TelemetryDB


class ReflectionAnalyzer:
    """Analyze your knowledge for introspection and self-understanding."""

    def __init__(
        self,
        graph_builder: GraphBuilder,
        ideas: List[Idea],
        telemetry: TelemetryDB,
    ):
        """Initialize analyzer.

        Args:
            graph_builder: Built knowledge graph
            ideas: All ideas from vault
            telemetry: Telemetry database for query history
        """
        self.graph = graph_builder.graph
        self.ideas = {str(idea.id): idea for idea in ideas}
        self.telemetry = telemetry

    def get_core_concepts(self, top_k: int = 5) -> List[Tuple[str, int]]:
        """Get your core concepts by connectivity.

        Args:
            top_k: Number of top concepts

        Returns:
            List of (concept_name, connection_count) tuples
        """
        # In-degree (how many things reference this concept)
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())

        # Combined score: how connected is this concept?
        scores = {}
        for node_id in self.graph.nodes():
            scores[node_id] = in_degrees.get(node_id, 0) + out_degrees.get(node_id, 0)

        # Get labels
        results = []
        for node_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]:
            label = self.graph.nodes[node_id].get("label", node_id)
            results.append((label, score))

        return results

    def get_blindspots(self, min_connections: int = 1) -> List[str]:
        """Identify concepts you haven't connected much.

        Args:
            min_connections: Max connections to be considered isolated

        Returns:
            List of isolated concept names
        """
        blindspots = []

        for node_id in self.graph.nodes():
            degree = self.graph.degree(node_id)
            if degree <= min_connections:
                label = self.graph.nodes[node_id].get("label", node_id)
                blindspots.append(label)

        return blindspots

    def get_suggestion_connections(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Suggest connections you should explore.

        Finds pairs of concepts that should probably be connected but aren't.

        Args:
            top_k: Number of suggestions

        Returns:
            List of dicts with source, target, reason
        """
        suggestions = []

        # Find nodes with similar neighborhoods that aren't connected
        nodes = list(self.graph.nodes())
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1 :]:
                # Skip if already connected
                if self.graph.has_edge(node1, node2) or self.graph.has_edge(
                    node2, node1
                ):
                    continue

                # Get neighbors
                neighbors1 = set(self.graph.successors(node1))
                neighbors2 = set(self.graph.successors(node2))

                # If they share neighbors, suggest connecting them
                shared = neighbors1 & neighbors2
                if len(shared) >= 2:  # Share at least 2 neighbors
                    label1 = self.graph.nodes[node1].get("label", node1)
                    label2 = self.graph.nodes[node2].get("label", node2)
                    shared_names = [
                        self.graph.nodes[s].get("label", s) for s in shared
                    ]

                    suggestions.append(
                        {
                            "source": label1,
                            "target": label2,
                            "reason": f"Both relate to: {', '.join(list(shared_names)[:2])}",
                            "shared_count": len(shared),
                        }
                    )

        # Sort by shared connections
        suggestions.sort(key=lambda x: x["shared_count"], reverse=True)
        return suggestions[:top_k]

    def get_thinking_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in what you ask about.

        Returns:
            Dict with query patterns
        """
        top_queries = self.telemetry.get_top_queries(limit=10)

        # Extract common topics/keywords
        keywords = {}
        for query in top_queries:
            q = query["query"].lower()
            # Simple keyword extraction
            for word in q.split():
                if len(word) > 3:  # Skip short words
                    keywords[word] = keywords.get(word, 0) + 1

        # Sort by frequency
        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "top_queries": top_queries[:5],
            "top_keywords": [k[0] for k in top_keywords],
            "total_queries": sum(q["count"] for q in top_queries),
        }

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get high-level summary of your knowledge.

        Returns:
            Dict with summary stats
        """
        return {
            "total_concepts": self.graph.number_of_nodes(),
            "total_connections": self.graph.number_of_edges(),
            "graph_density": nx.density(self.graph),
            "avg_connections_per_concept": (
                2 * self.graph.number_of_edges() / max(1, self.graph.number_of_nodes())
            ),
            "most_connected": self.get_core_concepts(top_k=1)[0][0]
            if self.get_core_concepts(top_k=1)
            else "N/A",
        }

    def get_full_reflection(self) -> Dict[str, Any]:
        """Get comprehensive reflection on your knowledge.

        Returns:
            Full reflection report
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": self.get_knowledge_summary(),
            "core_concepts": self.get_core_concepts(top_k=5),
            "blindspots": self.get_blindspots(),
            "suggested_connections": self.get_suggestion_connections(top_k=5),
            "thinking_patterns": self.get_thinking_patterns(),
        }
