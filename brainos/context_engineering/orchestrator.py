"""Context orchestration: filling three-layer context stack.

ContextOrchestrator assembles the Karpathy-style three-layer context window:
  1. Instruction Layer (highest priority): Persona, values, tone, framework
  2. Knowledge Layer: Relevant facts from hybrid retrieval, packed under budget
  3. Tool Layer (lowest priority): Available tool manifest

The orchestrator ensures the total token count never exceeds BudgetSpec.total_tokens,
and each layer respects its own sub-budget. This maximizes the signal-to-noise
ratio in the LLM context window.

Used by ResearchAgent, DraftingAgent, and the MCP server to build context
before calling the LLM.
"""

from typing import List

from brainos.context_engineering.selection import HybridRetriever
from brainos.context_engineering.packing import GreedyContextPacker
from brainos.core.models import BudgetSpec, ContextLayer, ContextSlice, PersonaBlock


class ContextOrchestrator:
    """Orchestrates Karpathy-style context engineering for three-layer stacking."""

    def __init__(
        self,
        retriever: HybridRetriever,
        packer: GreedyContextPacker,
        persona: PersonaBlock,
    ):
        """Initialize orchestrator.

        Args:
            retriever: Hybrid retrieval engine
            packer: Context packer
            persona: Instruction layer persona
        """
        self.retriever = retriever
        self.packer = packer
        self.persona = persona

    def orchestrate(
        self, query: str, budget: BudgetSpec = None
    ) -> List[ContextSlice]:
        """Fill context window with three layers optimally.

        Fills context in order: Instruction → Knowledge → Tools

        Args:
            query: User query/task
            budget: Token budget (defaults to standard)

        Returns:
            List of ContextSlice ready for context window
        """
        if budget is None:
            budget = BudgetSpec()

        slices: List[ContextSlice] = []

        # Layer 1: Instruction Layer
        # Persona, values, decision framework (always included)
        instruction_slice = ContextSlice(
            layer=ContextLayer.INSTRUCTION,
            content=self._build_instruction_block(),
            token_count=self._estimate_tokens(self._build_instruction_block()),
            source="persona_block",
            relevance_score=1.0,
        )

        if instruction_slice.token_count <= budget.instruction_budget:
            slices.append(instruction_slice)

        # Layer 2: Knowledge Layer
        # Retrieve and pack knowledge results
        facts = self.retriever.retrieve(query, top_k=10)
        packed_knowledge = self.packer.pack(facts, budget)

        for slice_obj in packed_knowledge:
            if sum(s.token_count for s in slices) + slice_obj.token_count <= budget.total_tokens:
                slices.append(slice_obj)

        # Layer 3: Tool Layer (Manifest)
        # List available tools/capabilities
        tool_slice = ContextSlice(
            layer=ContextLayer.TOOLS,
            content=self._build_tool_manifest(),
            token_count=self._estimate_tokens(self._build_tool_manifest()),
            source="tool_manifest",
            relevance_score=0.9,
        )

        if sum(s.token_count for s in slices) + tool_slice.token_count <= budget.total_tokens:
            slices.append(tool_slice)

        return slices

    def _build_instruction_block(self) -> str:
        """Build the instruction layer content.

        Returns:
            Formatted instruction block
        """
        values_str = ", ".join(self.persona.values)
        return f"""You are a {self.persona.name}.

Core Values: {values_str}
Tone: {self.persona.tone}
Reasoning Style: {self.persona.reasoning_style}
Decision Framework: {self.persona.decision_framework}

"""

    def _build_tool_manifest(self) -> str:
        """Build the tool layer content (available tools/capabilities).

        Returns:
            Formatted tool manifest
        """
        return """Available Tools:
- ask <query>: Query the knowledge vault
- graph-stats: Show knowledge graph topology
- reflect: Run daily reflection over your knowledge

You can compose these tools to build complex workflows.
"""

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)
