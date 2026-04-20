"""Knowledge layer: vault ingestion, embeddings, vectors, and graphs.

This package transforms raw Obsidian markdown into a queryable knowledge system:
  1. VaultAdapter reads markdown + frontmatter + WikiLinks
  2. Chunker splits text into embeddable segments
  3. Embedder generates vector representations
  4. VectorStore persists embeddings for semantic search
  5. GraphBuilder constructs a NetworkX graph from links and tags
  6. RAGEngine combines semantic + graph retrieval
  7. IngestionPipeline wires all steps into a single end-to-end flow

Abstract base classes (AbstractChunker, AbstractEmbedder, AbstractVectorStore)
allow swapping implementations without changing downstream code.
"""
