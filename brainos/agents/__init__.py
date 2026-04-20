"""Agentic framework: task execution and workflows.

This package implements the agentic layer of Second Brain OS:
  - AbstractAgent: Base contract for all agents (async run(task) -> AgentResult)
  - ResearchAgent: Investigates topics by synthesizing knowledge from the vault
  - DraftingAgent: Writes content (essays, summaries, outlines) grounded in facts
  - ReflectionAgent: Introspects on knowledge graph for self-understanding
  - PublishingAgent: Formats and exports content to markdown/txt
  - ReflectionAnalyzer: Graph analytics engine behind ReflectionAgent
  - AgentOrchestrator: Routes tasks and composes multi-agent workflows

Agents consume context from the ContextOrchestrator and call Anthropic's Claude
API for reasoning and generation. All agent activity is logged to telemetry.
"""
