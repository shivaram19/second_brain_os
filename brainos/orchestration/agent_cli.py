"""CLI for running agent workflows.

Agent-focused CLI exposing multi-step and single-agent operations:
  - research: Run ResearchAgent on a topic
  - draft: Run DraftingAgent to write content
  - research-draft: Compose research then draft
  - full-workflow: Research, draft, and publish to file
  - reflect: Run reflection and show insights
  - daily: Run the daily workflow (reflect + export + plan)

This CLI demonstrates how AgentOrchestrator composes agents into pipelines.
It is registered as a secondary entry point for power users who want to
run workflows directly without Claude Desktop.

Example usage:
    python -m brainos.orchestration.agent_cli research "AI safety"
    python -m brainos.orchestration.agent_cli full-workflow "Long-termism"
"""

import argparse
import json

from brainos.agents.orchestrator import AgentOrchestrator


def cmd_research(args):
    """Run research agent."""
    orchestrator = AgentOrchestrator()
    result = orchestrator.research(args.topic, depth=args.depth)

    if result["status"] == "success":
        print(f"\n📚 Research: {args.topic}\n")
        print(result["output"])
        print(f"\n📊 Tokens used: {result['tokens_used']}")
        print(f"📍 Sources: {result['context_sources']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def cmd_draft(args):
    """Run drafting agent."""
    orchestrator = AgentOrchestrator()
    result = orchestrator.draft(args.topic, format_type=args.format, length=args.length)

    if result["status"] == "success":
        print(f"\n✍️  Draft: {args.topic}\n")
        print(result["output"])
        print(f"\n📊 Tokens used: {result['tokens_used']}")
        print(f"📍 Sources: {result['context_sources']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def cmd_research_draft(args):
    """Run research + draft workflow."""
    orchestrator = AgentOrchestrator()
    result = orchestrator.research_and_draft(args.topic, format_type=args.format)

    if result["status"] == "success":
        print(f"\n🔍 Research & Draft: {args.topic}\n")
        print("=" * 60)
        print("RESEARCH INSIGHTS")
        print("=" * 60)
        print(result["research_insights"])
        print("\n" + "=" * 60)
        print("DRAFT")
        print("=" * 60)
        print(result["draft"])
        print(f"\n📊 Total tokens: {result['tokens_used']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def cmd_research_draft_publish(args):
    """Run full workflow: research, draft, publish."""
    orchestrator = AgentOrchestrator()
    result = orchestrator.research_draft_and_publish(
        args.topic, format_type=args.format, publish_format=args.publish_format
    )

    if result["status"] == "success":
        print(f"\n🚀 Full Workflow: {args.topic}\n")
        print("✅ Research completed")
        print("✅ Draft created")
        print(f"✅ Published to: {result['published']}")
        print(f"\n📊 Tokens used: {result['tokens_used']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def cmd_reflect(args):
    """Run reflection workflow."""
    orchestrator = AgentOrchestrator()
    result = orchestrator.reflect_on_knowledge()

    if result["status"] == "success":
        reflection = result["reflection"]
        print("\n🧠 Knowledge Reflection\n")

        summary = reflection.get("summary", {})
        print("📊 Summary:")
        print(f"  Concepts: {summary.get('total_concepts')}")
        print(f"  Connections: {summary.get('total_connections')}")
        print(f"  Density: {summary.get('graph_density', 0):.2%}")

        if reflection.get("core_concepts"):
            print("\n🌟 Core Concepts:")
            for i, (concept, score) in enumerate(reflection["core_concepts"][:5], 1):
                print(f"  {i}. {concept} ({score} connections)")

        if reflection.get("blindspots"):
            print("\n⚠️  Blindspots:")
            for blindspot in reflection["blindspots"][:5]:
                print(f"  - {blindspot}")

        if reflection.get("suggested_connections"):
            print("\n🔗 Suggested Connections:")
            for sugg in reflection["suggested_connections"][:3]:
                print(f"  - {sugg['source']} ↔ {sugg['target']}")
                print(f"    {sugg['reason']}")

    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def cmd_daily(args):
    """Run daily workflow."""
    orchestrator = AgentOrchestrator()
    result = orchestrator.daily_workflow()

    if result["status"] == "success":
        print("\n📅 Daily Workflow\n")
        print("✅ Reflection exported")
        print(f"   File: {result['reflection_file']}")
        print(f"\n🎯 Core Concepts Today:")
        for concept in result.get("core_concepts", []):
            print(f"   - {concept}")
        print(f"\n🔍 Suggested Explorations:")
        for topic in result.get("suggested_explorations", []):
            print(f"   - {topic}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Second Brain OS Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Research command
    research_parser = subparsers.add_parser("research", help="Research a topic")
    research_parser.add_argument("topic", help="Topic to research")
    research_parser.add_argument("--depth", default="medium", choices=["shallow", "medium", "deep"])

    # Draft command
    draft_parser = subparsers.add_parser("draft", help="Draft content")
    draft_parser.add_argument("topic", help="Topic to write about")
    draft_parser.add_argument("--format", default="essay",
                             choices=["essay", "summary", "article", "outline", "brainstorm"])
    draft_parser.add_argument("--length", default="medium", choices=["short", "medium", "long"])

    # Research + Draft command
    rd_parser = subparsers.add_parser("research-draft", help="Research then draft")
    rd_parser.add_argument("topic", help="Topic to research and write about")
    rd_parser.add_argument("--format", default="essay")

    # Full workflow command
    full_parser = subparsers.add_parser("full-workflow", help="Research, draft, and publish")
    full_parser.add_argument("topic", help="Topic to process")
    full_parser.add_argument("--format", default="essay")
    full_parser.add_argument("--publish-format", default="markdown", choices=["markdown", "txt"])

    # Reflect command
    subparsers.add_parser("reflect", help="Reflect on your knowledge")

    # Daily command
    subparsers.add_parser("daily", help="Run daily workflow")

    args = parser.parse_args()

    if args.command == "research":
        cmd_research(args)
    elif args.command == "draft":
        cmd_draft(args)
    elif args.command == "research-draft":
        cmd_research_draft(args)
    elif args.command == "full-workflow":
        cmd_research_draft_publish(args)
    elif args.command == "reflect":
        cmd_reflect(args)
    elif args.command == "daily":
        cmd_daily(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
