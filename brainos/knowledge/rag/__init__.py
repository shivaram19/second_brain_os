"""RAG (Retrieval-Augmented Generation) engine.

The RAGEngine implements hybrid retrieval by combining:
  - Semantic search: Vector similarity over chunk embeddings (ChromaDB)
  - Graph traversal: Neighborhood expansion from top semantic results (NetworkX)

This dual approach captures both semantic relevance and structural importance,
fixing the "lost-in-translation" problem of pure vector search.

RetrievedFacts contains both semantic_results (Chunk objects) and
graph_results (GraphNode objects), which are later packed into context slices.
"""
