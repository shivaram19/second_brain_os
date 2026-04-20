"""Knowledge ingestion pipeline.

The ingestion pipeline is the ETL layer of Second Brain OS:
  - Extract: Read all markdown notes from the Obsidian vault
  - Transform: Chunk text, generate embeddings
  - Load: Store vectors in ChromaDB and build the NetworkX graph

IngestionPipeline orchestrates VaultAdapter -> Chunker -> Embedder ->
VectorStore + GraphBuilder in a single call, returning stats about what
was processed.
"""
