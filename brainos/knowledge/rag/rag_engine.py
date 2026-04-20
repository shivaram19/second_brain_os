"""RAG engine combining semantic search and graph traversal.

RAGEngine implements hybrid retrieval for Second Brain OS:
  1. Semantic retrieval: Embed the query and search ChromaVectorStore for
     the most similar chunks.
  2. Graph traversal: Starting from the top semantic result's parent Idea,
     expand into the knowledge graph to find structurally related concepts.

This combines the strengths of vector search (semantic similarity) and
graph search (structural relationships), surfacing results that either
method alone might miss.

Used by HybridRetriever (context_engineering) and VaultMCPServer (mcp_servers).
"""

from brainos.core.models import RetrievedFacts, Chunk, GraphNode
from brainos.knowledge.vector_store_base import AbstractVectorStore
from brainos.knowledge.embedding_base import AbstractEmbedder
from brainos.knowledge.graph.graph_builder import GraphBuilder


class RAGEngine:
    """Hybrid retrieval combining vector search and graph traversal."""

    def __init__(
        self,
        vector_store: AbstractVectorStore,
        embedder: AbstractEmbedder,
        graph_builder: GraphBuilder,
    ):
        """Initialize RAG engine.

        Args:
            vector_store: Vector store for semantic search
            embedder: Embedder for converting queries to vectors
            graph_builder: Graph builder for structural retrieval
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.graph = graph_builder.graph
        self.idea_map = {}  # node_id -> Idea (populated during ingestion)

    def set_idea_map(self, idea_map: dict):
        """Set mapping from node IDs to Ideas (for graph enrichment).

        Args:
            idea_map: Dict mapping node_id -> Idea
        """
        self.idea_map = idea_map

    def retrieve(self, query: str, top_k: int = 10) -> RetrievedFacts:
        """Retrieve facts using hybrid approach.

        Args:
            query: Natural language query
            top_k: Number of results per retrieval method

        Returns:
            RetrievedFacts with semantic and graph results
        """
        # Semantic retrieval
        query_embedding = self.embedder.embed(query)
        semantic_results = self.vector_store.search(query_embedding, top_k=top_k)

        # Graph traversal: start from top semantic result and expand neighborhood
        graph_results = []
        if semantic_results:
            # Use top semantic result as starting point
            top_chunk = semantic_results[0]
            neighbors = self._get_neighbors_from_chunk(top_chunk, depth=2, top_k=top_k)
            graph_results = neighbors

        return RetrievedFacts(
            query=query,
            semantic_results=semantic_results,
            graph_results=graph_results,
            metadata={"method": "hybrid"},
        )

    def _get_neighbors_from_chunk(
        self, chunk: Chunk, depth: int = 2, top_k: int = 10
    ) -> list[GraphNode]:
        """Get graph neighbors for a chunk's parent idea.

        Args:
            chunk: Chunk to start from
            depth: Traversal depth
            top_k: Max results

        Returns:
            List of GraphNode neighbors
        """
        node_id = str(chunk.idea_id)
        if node_id not in self.graph:
            return []

        # Get neighbors
        neighbors = []
        visited = set()
        to_visit = [(node_id, 0)]

        while to_visit and len(neighbors) < top_k:
            current, current_depth = to_visit.pop(0)
            if current in visited or current_depth >= depth:
                continue

            visited.add(current)

            # Add this node as a GraphNode
            node_data = self.graph.nodes[current]
            graph_node = GraphNode(
                node_id=current,
                label=node_data.get("label", ""),
                node_type=node_data.get("node_type", "idea"),
                properties=dict(node_data),
            )
            if current != node_id:  # Don't include the starting node
                neighbors.append(graph_node)

            # Add successors to visit queue
            for successor in self.graph.successors(current):
                if successor not in visited:
                    to_visit.append((successor, current_depth + 1))

        return neighbors[:top_k]
