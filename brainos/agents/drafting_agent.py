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

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

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

    def __init__(self, api_key: str = None, provider: str = "auto"):
        """Initialize drafting agent.

        Args:
            api_key: API key for the chosen provider
            provider: LLM provider — 'anthropic', 'moonshot', or 'auto'
        """
        self.config = load_config()
        self.provider = provider
        self.client = self._init_client(api_key)

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

    def _init_client(self, api_key: str = None):
        """Initialize LLM client based on provider."""
        if self.provider == "auto":
            if HAS_ANTHROPIC:
                return Anthropic(api_key=api_key)
            try:
                from brainos.core.moonshot_client import MoonshotClient
                return MoonshotClient(api_key=api_key)
            except (ImportError, ValueError):
                raise RuntimeError(
                    "No LLM provider available. Install anthropic or set MOONSHOT_API_KEY."
                )
        elif self.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise RuntimeError("Anthropic package not installed.")
            return Anthropic(api_key=api_key)
        elif self.provider == "moonshot":
            from brainos.core.moonshot_client import MoonshotClient
            return MoonshotClient(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 3000):
        """Call LLM with provider-agnostic interface."""
        if hasattr(self.client, "messages"):
            # Anthropic interface
            return self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        else:
            # Moonshot interface
            return self.client.messages.create(
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=max_tokens,
            )

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
            response = self._call_llm(
                system_prompt,
                f"{context_text}\n\n{user_prompt}",
                max_tokens=3000,
            )

            output = response.content[0].text

            input_tokens = getattr(response.usage, "input_tokens", response.usage.get("input_tokens", 0))
            output_tokens = getattr(response.usage, "output_tokens", response.usage.get("output_tokens", 0))
            total_tokens = input_tokens + output_tokens

            self.telemetry.log_event(
                "draft",
                query=topic,
                num_results=len(context_slices),
                tokens_used=total_tokens,
            )

            return {
                "status": "success",
                "topic": topic,
                "format": format_type,
                "length": length,
                "output": output,
                "tokens_used": total_tokens,
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
