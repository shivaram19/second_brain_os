"""Abstract base class for hybrid retrieval.

Retrievers bridge the knowledge layer and context engineering layer.
They execute hybrid searches (semantic + graph) and return RetrievedFacts,
which are then passed to a context packer for budget-aware selection.

AbstractRetriever allows swapping retrieval strategies (e.g., pure semantic,
weighted hybrid, multi-hop graph) without changing the orchestration logic.
"""

from abc import ABC, abstractmethod

from brainos.core.models import RetrievedFacts


class AbstractRetriever(ABC):
    """Base class for hybrid retrieval (semantic + graph)."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10) -> RetrievedFacts:
        """Retrieve facts relevant to a query using hybrid methods.

        Args:
            query: Natural language query
            top_k: Number of top results to return

        Returns:
            RetrievedFacts with semantic and graph results
        """
