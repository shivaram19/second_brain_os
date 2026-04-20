"""Abstract base class for context packing.

Context packers take RetrievedFacts and a BudgetSpec, then select and order
context slices to maximize relevance while staying under token budget.

This is an NP-hard optimization problem in general; implementations use
heuristics (greedy by relevance score, knapsack-style, etc.). The abstraction
allows experimenting with different packing algorithms without touching
the orchestrator or agents.
"""

from abc import ABC, abstractmethod
from typing import List

from brainos.core.models import BudgetSpec, ContextSlice, RetrievedFacts


class AbstractContextPacker(ABC):
    """Base class for budget-aware context packing."""

    @abstractmethod
    def pack(
        self, candidates: RetrievedFacts, budget: BudgetSpec
    ) -> List[ContextSlice]:
        """Pack retrieved facts into context slices respecting token budget.

        Args:
            candidates: Retrieved facts from retrieval
            budget: Token budget specification

        Returns:
            List of ContextSlice objects ordered by priority, under budget
        """
