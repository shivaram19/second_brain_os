"""Budget-aware context packing.

GreedyContextPacker implements a fast heuristic for token-aware context
packing. It converts semantic results (Chunks) and graph results (GraphNodes)
into ContextSlices, scores them by relevance, and greedily packs the highest-
scoring slices until the knowledge budget is exhausted.

Scoring is simple but effective for MVP:
  - Semantic results: score decreases with rank (top result = 1.0)
  - Graph results: fixed lower score, decreasing with rank

Trade-off: Greedy packing is fast (O(n log n)) but not optimal. More
sophisticated algorithms (knapsack DP, constrained optimization) can be
plugged in via AbstractContextPacker later.
"""

from typing import List

from brainos.context_engineering.packer_base import AbstractContextPacker
from brainos.core.models import BudgetSpec, ContextLayer, ContextSlice, RetrievedFacts


class GreedyContextPacker(AbstractContextPacker):
    """Greedy token-aware context packer."""

    def pack(
        self, candidates: RetrievedFacts, budget: BudgetSpec
    ) -> List[ContextSlice]:
        """Pack candidates into context slices under token budget.

        Uses a simple greedy approach: score by relevance × recency × novelty,
        then pack in order of highest score until budget exhausted.

        Args:
            candidates: Retrieved facts
            budget: Token budget

        Returns:
            List of ContextSlice ordered by score
        """
        if not budget.validate():
            raise ValueError("Budget does not validate: total > sum of layers")

        slices: List[ContextSlice] = []

        # Convert semantic results to context slices
        for i, chunk in enumerate(candidates.semantic_results):
            # Simple scoring: inverse of position (closer to top = higher score)
            # Rough token count: 1 token ≈ 4 characters
            token_count = max(1, len(chunk.text) // 4)
            relevance_score = 1.0 - (i / max(1, len(candidates.semantic_results)))

            slice_obj = ContextSlice(
                layer=ContextLayer.KNOWLEDGE,
                content=chunk.text,
                token_count=token_count,
                source=f"semantic_result_{i}",
                relevance_score=relevance_score,
            )
            slices.append(slice_obj)

        # Convert graph results to context slices
        for i, node in enumerate(candidates.graph_results):
            token_count = 20  # Estimate for node labels
            relevance_score = 0.5 - (i / max(1, len(candidates.graph_results) * 2))

            slice_obj = ContextSlice(
                layer=ContextLayer.KNOWLEDGE,
                content=f"Related Concept: {node.label}",
                token_count=token_count,
                source=f"graph_result_{i}",
                relevance_score=relevance_score,
            )
            slices.append(slice_obj)

        # Sort by relevance score (greedy: highest first)
        slices.sort(key=lambda s: s.relevance_score, reverse=True)

        # Greedily pack under knowledge budget
        packed = []
        used_tokens = 0

        for slice_obj in slices:
            if used_tokens + slice_obj.token_count <= budget.knowledge_budget:
                packed.append(slice_obj)
                used_tokens += slice_obj.token_count
            # else skip (exhausted budget)

        return packed
