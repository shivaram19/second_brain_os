"""Build and manage knowledge graphs from vault ideas.

GraphBuilder constructs a NetworkX DiGraph from Obsidian notes by:
  - Adding each Idea as a typed node (idea, concept, project, etc.)
  - Creating edges from WikiLinks ([[note-name]]) between notes
  - Creating bidirectional edges between Ideas sharing tags

The graph enables structural retrieval (neighbors, centrality) that
complements pure vector similarity. ReflectionAgent uses graph analytics
to identify core concepts, blindspots, and suggested connections.

Trade-off: NetworkX is in-memory and fast for personal-scale graphs
(10k–100k nodes), but would need migration to Neo4j for >1M nodes.
"""

from typing import Dict, List, Set
import networkx as nx

from brainos.core.models import Idea, GraphNode, GraphEdge, EdgeType, NodeType
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter


class GraphBuilder:
    """Construct knowledge graphs from Obsidian vault."""

    def __init__(self):
        """Initialize graph builder."""
        self.graph = nx.DiGraph()

    def build_from_ideas(self, ideas: List[Idea]) -> nx.DiGraph:
        """Build graph from a list of Ideas.

        Args:
            ideas: List of Ideas from vault

        Returns:
            NetworkX DiGraph with nodes and edges
        """
        # Add nodes for each idea
        for idea in ideas:
            node_id = str(idea.id)
            self.graph.add_node(
                node_id,
                label=idea.title,
                node_type=NodeType.IDEA,
                tags=idea.tags,
                vault_path=idea.vault_path,
            )

        # Build index: title -> node_id for WikiLink resolution
        title_to_id = {idea.title: str(idea.id) for idea in ideas}

        # Add edges from WikiLinks
        vault_adapter = VaultAdapter("~/ObsidianVault")  # dummy for link extraction
        for idea in ideas:
            source_id = str(idea.id)
            links = vault_adapter.extract_wikilinks(idea.content)

            for link in links:
                # Try to find target by title
                target_id = title_to_id.get(link)
                if target_id:
                    self.graph.add_edge(source_id, target_id, edge_type=EdgeType.LINKS_TO)

        # Add edges from tags (if a tag appears in multiple ideas, connect them)
        tag_to_ideas: Dict[str, Set[str]] = {}
        for idea in ideas:
            idea_id = str(idea.id)
            for tag in idea.tags:
                if tag not in tag_to_ideas:
                    tag_to_ideas[tag] = set()
                tag_to_ideas[tag].add(idea_id)

        for tag, idea_ids in tag_to_ideas.items():
            idea_list = sorted(idea_ids)
            # Connect all ideas with same tag (bidirectional)
            for i, id1 in enumerate(idea_list):
                for id2 in idea_list[i + 1 :]:
                    self.graph.add_edge(id1, id2, edge_type=EdgeType.RELATES_TO, weight=0.5)
                    self.graph.add_edge(id2, id1, edge_type=EdgeType.RELATES_TO, weight=0.5)

        return self.graph

    def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]:
        """Get neighbors of a node up to a given depth.

        Args:
            node_id: Node to query
            depth: Depth of traversal

        Returns:
            List of neighbor node IDs
        """
        if node_id not in self.graph:
            return []

        neighbors = set()
        to_visit = [(node_id, 0)]

        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current_depth >= depth:
                continue

            for neighbor in self.graph.successors(current):
                if neighbor != node_id:
                    neighbors.add(neighbor)
                    to_visit.append((neighbor, current_depth + 1))

        return list(neighbors)

    def get_node_stats(self) -> Dict[str, int]:
        """Get basic graph statistics.

        Returns:
            Dict with node count, edge count, density
        """
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
        }

    def pagerank(self, top_k: int = 10) -> List[tuple[str, float]]:
        """Get top-K nodes by in-degree (simplified centrality).

        Args:
            top_k: Number of top nodes

        Returns:
            List of (node_id, rank) tuples
        """
        # Use in-degree as a simple centrality measure (no scipy dependency)
        degrees = dict(self.graph.in_degree(weight="weight"))
        sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_degrees[:top_k]
