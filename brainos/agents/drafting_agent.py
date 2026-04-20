"""Drafting Agent - Writes content from knowledge base.

The DraftingAgent produces written content grounded in the user's actual
knowledge vault. It supports multiple formats:
  - essay, summary, article, outline, brainstorm

And lengths:
  - short (~500 words), medium (~1500 words), long (~3000 words)

Like the ResearchAgent, it uses ContextOrchestrator to retrieve relevant
facts and persona context, then calls Claude API to generate original,
cited content. This ensures outputs are aligned with the user's values,
tone, and existing knowledge rather than generic LLM hallucinations.
"""

from typing import Any, Dict

from anthropic import Anthropic

from brainos.context_engineering.orchestrator import ContextOrchestrator
from brainos.context_engineering.packing import GreedyContextPacker
from brainos.context_engineering.selection import HybridRetriever
from brainos.core import load_config
from brainos.core.models import BudgetSpec, PersonaBlock
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.knowledge.embedding.sentence_transformers_embedder import (
    SentenceTransformersEmbedder,
)
from brainos.knowledge.vector_store.chroma_store import ChromaVectorStore
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.knowledge.rag.rag_engine import RAGEngine
from brainos.telemetry.schema import TelemetryDB


class DraftingAgent:
    """Agent that writes content based on knowledge base."""

    def __init__(self, api_key: str = None):
        """Initialize drafting agent.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.config = load_config()

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

        persona_config = self.config.persona
        self.persona = PersonaBlock(
            name=persona_config.get("name", "Drafting Agent"),
            values=persona_config.get("values", []),
            tone=persona_config.get("tone", "clear, engaging, well-structured"),
            reasoning_style=persona_config.get("reasoning_style", ""),
            decision_framework=persona_config.get("decision_framework", ""),
        )

        self.orchestrator = ContextOrchestrator(self.retriever, self.packer, self.persona)

    def draft(
        self, topic: str, format_type: str = "essay", length: str = "medium"
    ) -> Dict[str, Any]:
        """Draft content on a topic.

        Args:
            topic: Topic to write about
            format_type: "essay", "summary", "article", "outline", "brainstorm"
            length: "short" (500), "medium" (1500), "long" (3000)

        Returns:
            Dict with drafted content
        """
        # Token budgets by length
        token_budgets = {"short": 50000, "medium": 100000, "long": 150000}
        word_counts = {"short": 500, "medium": 1500, "long": 3000}

        budget = BudgetSpec(
            total_tokens=token_budgets[length],
            instruction_budget=token_budgets[length] // 6,
            knowledge_budget=token_budgets[length] // 2,
            tool_budget=token_budgets[length] // 6,
        )

        context_slices = self.orchestrator.orchestrate(topic, budget)
        context_text = self._build_context(context_slices)

        system_prompt = f"""You are a professional writer. Your role is to create well-structured, engaging content.

Persona: {self.persona.name}
Values: {', '.join(self.persona.values)}
Tone: {self.persona.tone}

Use the provided knowledge base context to write original, insightful content. Always cite sources from your knowledge base."""

        format_instructions = {
            "essay": "Write a well-structured essay with introduction, body, and conclusion.",
            "summary": "Write a concise summary capturing the key points.",
            "article": "Write a journalistic article with headlines and engaging prose.",
            "outline": "Create a detailed outline with main points and sub-points.",
            "brainstorm": "Generate creative ideas and connections around this topic.",
        }

        user_prompt = f"""Please write a {format_type} about: {topic}

Length: approximately {word_counts[length]} words
Format: {format_instructions.get(format_type, 'well-structured content')}

Use the provided context to create original, high-quality content. Cite any concepts or ideas from the knowledge base."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"{context_text}\n\n{user_prompt}",
                    }
                ],
            )

            output = response.content[0].text

            self.telemetry.log_event(
                "draft",
                query=topic,
                num_results=len(context_slices),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            )

            return {
                "status": "success",
                "topic": topic,
                "format": format_type,
                "length": length,
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
        """Build context for Claude."""
        context_parts = []
        for slice_obj in context_slices:
            context_parts.append(f"[{slice_obj.layer.value.upper()}]\n{slice_obj.content}\n")
        return "\n---\n".join(context_parts)
