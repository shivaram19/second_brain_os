"""Command-line interface for Second Brain OS.

Main user-facing CLI exposing core knowledge operations:
  - ingest: Load Obsidian vault into vectors and graph
  - ask: Query the knowledge base with hybrid retrieval
  - graph-stats: Show knowledge graph topology and top concepts
  - reflect: Run reflection agent for self-insight

This CLI is registered as the 'brainos' console script in pyproject.toml.
It is the primary way users interact with the system before (or alongside)
Claude Desktop MCP integration.

Example usage:
    brainos ingest
    brainos ask "How does systems thinking relate to effective altruism?"
    brainos graph-stats
    brainos reflect
"""

import argparse
import json
from pathlib import Path

from brainos.core import load_config
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.knowledge.chunking.heading_chunker import HeadingChunker
from brainos.knowledge.embedding.sentence_transformers_embedder import (
    SentenceTransformersEmbedder,
)
from brainos.knowledge.vector_store.chroma_store import ChromaVectorStore
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.knowledge.ingestion.pipeline import IngestionPipeline
from brainos.knowledge.rag.rag_engine import RAGEngine
from brainos.agents.reflection_agent import ReflectionAgent


def create_rag_engine():
    """Create a fully initialized RAG engine.

    Returns:
        RAGEngine instance
    """
    config = load_config()
    vault_path = config.paths.get("obsidian_vault", "~/ObsidianVault")
    vector_db_path = config.paths.get("vector_index_dir", "./.brainos/vector_db")

    vault_adapter = VaultAdapter(vault_path)
    chunker = HeadingChunker()
    embedder = SentenceTransformersEmbedder()
    vector_store = ChromaVectorStore(vector_db_path)
    graph_builder = GraphBuilder()

    rag_engine = RAGEngine(vector_store, embedder, graph_builder)
    return rag_engine, vault_adapter, graph_builder


def cmd_ingest(args):
    """Ingest vault into vectors and graph."""
    config = load_config()
    vault_path = config.paths.get("obsidian_vault", "~/ObsidianVault")
    vector_db_path = config.paths.get("vector_index_dir", "./.brainos/vector_db")

    print(f"📚 Ingesting vault from: {vault_path}")

    vault_adapter = VaultAdapter(vault_path)
    chunker = HeadingChunker()
    embedder = SentenceTransformersEmbedder()
    vector_store = ChromaVectorStore(vector_db_path)
    graph_builder = GraphBuilder()

    pipeline = IngestionPipeline(
        vault_adapter, chunker, embedder, vector_store, graph_builder
    )

    stats = pipeline.ingest_all()

    print("\n✅ Ingestion complete!")
    print(f"   Ideas loaded: {stats['ideas_loaded']}")
    print(f"   Chunks created: {stats['chunks_created']}")
    print(f"   Chunks embedded: {stats['chunks_embedded']}")
    print(f"   Graph nodes: {stats['graph_nodes']}")
    print(f"   Graph edges: {stats['graph_edges']}")


def cmd_ask(args):
    """Ask a question and get RAG results."""
    query = args.query
    top_k = args.top_k

    print(f"\n🔍 Asking: {query}\n")

    rag_engine, vault_adapter, graph_builder = create_rag_engine()

    # Try to retrieve results
    try:
        results = rag_engine.retrieve(query, top_k=top_k)

        print(f"📊 Retrieved {len(results.semantic_results)} semantic + {len(results.graph_results)} graph results\n")

        if results.semantic_results:
            print("🔹 Semantic Results:")
            for i, chunk in enumerate(results.semantic_results[:3], 1):
                preview = chunk.text[:200].replace("\n", " ") + "..."
                print(f"\n   [{i}] {chunk.metadata.get('title', 'Unknown')}")
                print(f"       {preview}")

        if results.graph_results:
            print("\n🔹 Related Concepts (Graph):")
            for i, node in enumerate(results.graph_results[:3], 1):
                print(f"   [{i}] {node.label}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Did you ingest the vault? Try: brainos ingest")


def cmd_graph_stats(args):
    """Show knowledge graph statistics."""
    config = load_config()
    vault_path = config.paths.get("obsidian_vault", "~/ObsidianVault")

    vault_adapter = VaultAdapter(vault_path)
    graph_builder = GraphBuilder()

    # Load ideas and build graph
    ideas = vault_adapter.ingest_all()
    if not ideas:
        print("⚠️  No ideas found. Run: brainos ingest")
        return

    graph_builder.build_from_ideas(ideas)

    stats = graph_builder.get_node_stats()
    top_k = graph_builder.pagerank(top_k=10)

    print(f"\n📈 Knowledge Graph Statistics:")
    print(f"   Nodes: {stats['nodes']}")
    print(f"   Edges: {stats['edges']}")
    print(f"   Density: {stats['density']:.4f}")

    print(f"\n🌟 Top Concepts by PageRank:")
    for i, (node_id, rank) in enumerate(top_k, 1):
        label = graph_builder.graph.nodes[node_id].get("label", node_id)
        print(f"   [{i}] {label} ({rank:.4f})")


def cmd_reflect(args):
    """Reflect on your knowledge and get insights."""
    config = load_config()
    vault_path = config.paths.get("obsidian_vault", "~/ObsidianVault")
    telemetry_db_path = config.paths.get("telemetry_db", "./.brainos/telemetry.db")

    try:
        agent = ReflectionAgent(vault_path, telemetry_db_path)
        reflection = agent.reflect_full()
        print(reflection)

        # Also log this reflection event
        from brainos.telemetry.schema import TelemetryDB

        telemetry = TelemetryDB(telemetry_db_path)
        telemetry.log_event("reflect", metadata={"reflection_type": "full"})

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Did you ingest the vault? Try: brainos ingest")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Second Brain OS - Local knowledge orchestration"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ingest command
    subparsers.add_parser("ingest", help="Ingest Obsidian vault")

    # ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("query", nargs="+", help="Question to ask")
    ask_parser.add_argument("--top-k", type=int, default=10, help="Top K results")

    # graph-stats command
    subparsers.add_parser("graph-stats", help="Show graph statistics")

    # reflect command
    subparsers.add_parser(
        "reflect", help="Reflect on your knowledge and get insights"
    )

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "ask":
        args.query = " ".join(args.query)
        cmd_ask(args)
    elif args.command == "graph-stats":
        cmd_graph_stats(args)
    elif args.command == "reflect":
        cmd_reflect(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
