"""Context engineering: selection, packing, and orchestration.

This package implements Karpathy-style "context as architecture" for Second
Brain OS. It fills the LLM context window optimally using a three-layer stack:

  1. Instruction Layer: Persona, values, decision framework (from config/persona.yaml)
  2. Knowledge Layer: Relevant facts retrieved via hybrid RAG
  3. Tool Layer: Available capabilities and tool manifest

Components:
  - HybridRetriever: Combines semantic + graph retrieval
  - GreedyContextPacker: Token-aware greedy packing under budget constraints
  - ContextOrchestrator: Assembles the three layers in priority order
"""
