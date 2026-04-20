"""Research Agent - Investigates topics and synthesizes knowledge.

The ResearchAgent answers questions and explores topics by:
  1. Loading persona/config from YAML
  2. Retrieving relevant context via ContextOrchestrator (hybrid RAG)
  3. Building a three-layer context window (instruction + knowledge + tools)
  4. Calling Claude API with persona-guided system prompts
  5. Logging usage to telemetry

Depth levels (shallow/medium/deep) adjust token budgets to trade speed
for thoroughness. Used standalone or as the first step in multi-agent
workflows (research → draft → publish).
"""

import json
from typing import Any, Dict

from anthropic import Anthropic

from brainos.context_engineering.orchestrator import ContextOrchestrator
from brainos.context_engineering.packing import GreedyContextPacker
from brainos.context_engineering.selection import HybridRetriever
from brainos.core import load_config
from brainos.core.models import AgentResult, BudgetSpec, PersonaBlock, TaskStatus
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.knowledge.chunking.heading_chunker import HeadingChunker
from brainos.knowledge.embedding.sentence_transformers_embedder import (
    SentenceTransformersEmbedder,
)
from brainos.knowledge.vector_store.chroma_store import ChromaVectorStore
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.knowledge.rag.rag_engine import RAGEngine
from brainos.telemetry.schema import TelemetryDB


class ResearchAgent:
    """Agent that researches topics by synthesizing knowledge."""

    def __init__(self, api_key: str = None):
        """Initialize research agent.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.client = Anthropic(api_key=api_key)
        self.config = load_config()

        # Load components
        vault_path = self.config.paths.get("obsidian_vault", "~/ObsidianVault")
        vector_db_path = self.config.paths.get("vector_index_dir", "./.brainos/vector_db")
        telemetry_db_path = self.config.paths.get("telemetry_db", "./.brainos/telemetry.db")

        self.vault_adapter = VaultAdapter(vault_path)
        self.embedder = SentenceTransformersEmbedder()
        self.vector_store = ChromaVectorStore(vector_db_path)
        self.graph_builder = GraphBuilder()

        self.rag_engine = RAGEngine(self.vector_store, self.embedder, self.graph_builder)
        self.retriever = HybridRetriever(self.rag_engine)
        self.packer = GreedyContextPacker()
        self.telemetry = TelemetryDB(telemetry_db_path)

        # Load persona
        persona_config = self.config.persona
        self.persona = PersonaBlock(
            name=persona_config.get("name", "Research Agent"),
            values=persona_config.get("values", []),
            tone=persona_config.get("tone", "analytical, thorough"),
            reasoning_style=persona_config.get("reasoning_style", "evidence-based"),
            decision_framework=persona_config.get("decision_framework", ""),
        )

        self.orchestrator = ContextOrchestrator(self.retriever, self.packer, self.persona)

    def research(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        """Research a topic by synthesizing knowledge.

        Args:
            topic: Topic to research
            depth: "shallow" (quick), "medium" (balanced), "deep" (thorough)

        Returns:
            Dict with research output
        """
        # Adjust token budget based on depth
        budget_tokens = {"shallow": 50000, "medium": 100000, "deep": 150000}[depth]

        budget = BudgetSpec(
            total_tokens=budget_tokens,
            instruction_budget=budget_tokens // 6,
            knowledge_budget=budget_tokens // 2,
            tool_budget=budget_tokens // 6,
        )

        # Get context
        context_slices = self.orchestrator.orchestrate(topic, budget)

        # Build context for Claude
        context_text = self._build_context(context_slices)

        # Query Claude
        system_prompt = f"""You are a research agent. Your role is to investigate topics thoroughly using the provided knowledge base.

Persona: {self.persona.name}
Values: {', '.join(self.persona.values)}
Tone: {self.persona.tone}
Reasoning Style: {self.persona.reasoning_style}

Use the provided context to synthesize a comprehensive research output. Cite sources from your knowledge base.
"""

        user_prompt = f"""Research the following topic in depth:

Topic: {topic}
Depth: {depth}

Using the provided context from the knowledge base, synthesize a thorough research summary that:
1. Defines the topic and its importance
2. Explains key concepts and relationships
3. Discusses practical applications
4. Identifies connections to other ideas
5. Suggests areas for further exploration

Format your response with clear sections and cite sources from the knowledge base."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"{context_text}\n\n{user_prompt}",
                    }
                ],
            )

            output = response.content[0].text

            # Log to telemetry
            self.telemetry.log_event(
                "research",
                query=topic,
                num_results=len(context_slices),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            )

            return {
                "status": "success",
                "topic": topic,
                "depth": depth,
                "output": output,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "context_sources": len(context_slices),
            }

        except Exception as e:
            return {
                "status": "error",
                "topic": topic,
                "error": str(e),
            }

    def _build_context(self, context_slices) -> str:
        """Build context text for Claude.

        Args:
            context_slices: List of ContextSlice objects

        Returns:
            Formatted context string
        """
        context_parts = []

        for slice_obj in context_slices:
            context_parts.append(f"[{slice_obj.layer.value.upper()}]\n{slice_obj.content}\n")

        return "\n---\n".join(context_parts)
