"""MCP servers for exposing vault, graph, and telemetry.

This package implements Model Context Protocol (MCP) servers that expose
Second Brain OS as tools and resources to Claude Desktop and Claude API.

MCP is Anthropic's open protocol for connecting LLMs to external data sources.
These servers enable Claude to query the user's personal knowledge base
without dumping the entire vault into context (100x token efficiency).

Servers:
  - SecondBrainMCPServer (claude_server.py): Production MCP server with
    tools (ask, reflect, search_notes, get_connections, graph_stats) and
    resources (vault index, persona, telemetry summary)
  - VaultMCPServer (vault_server.py): Early MVP stub showing the interface
  - run_server.py: Stdio transport wrapper implementing the MCP protocol
"""
