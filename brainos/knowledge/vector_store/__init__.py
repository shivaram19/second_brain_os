"""Vector store implementations.

Provides concrete vector database backends that implement AbstractVectorStore:
  - ChromaVectorStore: Production-ready, local-first, persistent storage

ChromaDB is the default because it requires no external services, supports
HNSW approximate nearest neighbors, and has a clean Python API. The abstraction
allows future migration to FAISS, Pinecone, or SQLite-vec without refactoring
calling code.
"""
