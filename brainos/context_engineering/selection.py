"""Hybrid retrieval combining semantic and graph-based selection.

HybridRetriever is the concrete implementation of AbstractRetriever that
delegates to the RAGEngine for hybrid semantic + graph retrieval.

It sits at the boundary between the knowledge layer and context engineering:
  - Knowledge layer: RAGEngine performs the actual vector/graph lookups
  - Context engineering: HybridRetriever exposes a clean interface for
    the ContextOrchestrator and agents to consume

This thin wrapper allows the RAG engine to evolve independently while
maintaining a stable contract upstream.
"""

from brainos.context_engineering.retriever_base import AbstractRetriever
from brainos.core.models import RetrievedFacts
from brainos.knowledge.rag.rag_engine import RAGEngine


class HybridRetriever(AbstractRetriever):
    """Retrieve facts using hybrid semantic + graph approach."""

    def __init__(self, rag_engine: RAGEngine):
        """Initialize retriever.

        Args:
            rag_engine: Configured RAG engine
        """
        self.rag_engine = rag_engine

    def retrieve(self, query: str, top_k: int = 10) -> RetrievedFacts:
        """Retrieve facts using the RAG engine's hybrid method.

        Args:
            query: Natural language query
            top_k: Number of results per method

        Returns:
            RetrievedFacts with combined results
        """
        return self.rag_engine.retrieve(query, top_k=top_k)
