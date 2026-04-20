#!/usr/bin/env python3
"""Run the Second Brain OS MCP server for Claude Desktop.

This script implements the Model Context Protocol (MCP) over stdio transport,
exposing Second Brain OS as tools and resources to Claude.

It reads JSON-RPC requests from stdin and writes responses to stdout, which
is the standard transport mechanism for MCP servers launched by Claude Desktop.

The MCPProtocol class handles the five core MCP methods:
  - initialize: Protocol handshake
  - tools/list: Expose available tool schemas
  - resources/list: Expose available resource URIs
  - tools/call: Execute a tool (ask, reflect, search_notes, etc.)
  - resources/read: Return resource contents

Usage:
    python -m brainos.mcp_servers.run_server
    # Or as configured in Claude Desktop MCP settings
"""

import json
import sys
from typing import Any

from brainos.mcp_servers.claude_server import SecondBrainMCPServer


class MCPProtocol:
    """Minimal MCP protocol implementation for stdio transport."""

    def __init__(self, server: SecondBrainMCPServer):
        """Initialize MCP protocol handler.

        Args:
            server: SecondBrainMCPServer instance
        """
        self.server = server
        self.server_version = "1.0"
        self.protocol_version = "2024-11-05"

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle incoming MCP request.

        Args:
            request: MCP request dict

        Returns:
            MCP response dict
        """
        jsonrpc = request.get("jsonrpc", "2.0")
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        try:
            # Initialize
            if method == "initialize":
                return self._handle_initialize(request_id, jsonrpc)

            # List available tools
            elif method == "tools/list":
                return self._handle_list_tools(request_id, jsonrpc)

            # List available resources
            elif method == "resources/list":
                return self._handle_list_resources(request_id, jsonrpc)

            # Call tool
            elif method == "tools/call":
                return self._handle_tool_call(request_id, jsonrpc, params)

            # Read resource
            elif method == "resources/read":
                return self._handle_resource_read(request_id, jsonrpc, params)

            else:
                return {
                    "jsonrpc": jsonrpc,
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }

        except Exception as e:
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            }

    def _handle_initialize(self, request_id: str, jsonrpc: str) -> dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "result": {
                "protocolVersion": self.protocol_version,
                "serverInfo": {
                    "name": "Second Brain OS",
                    "version": "0.2.0",
                },
                "capabilities": {
                    "tools": {},
                    "resources": {},
                },
            },
        }

    def _handle_list_tools(self, request_id: str, jsonrpc: str) -> dict[str, Any]:
        """List available tools."""
        tools = [
            {
                "name": "ask",
                "description": "Ask a question and get packed context from your knowledge base. Returns three-layer context (Instruction + Knowledge + Tools) optimized for your query.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Your question or task",
                        },
                        "budget_tokens": {
                            "type": "integer",
                            "description": "Total token budget (default: 100000)",
                            "default": 100000,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "reflect",
                "description": "Reflect on your knowledge: core concepts, blindspots, suggested connections, thinking patterns.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "search_notes",
                "description": "Search for notes matching a query.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_connections",
                "description": "Get related concepts for a given concept from your knowledge graph.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "concept": {
                            "type": "string",
                            "description": "Concept name",
                        },
                    },
                    "required": ["concept"],
                },
            },
            {
                "name": "graph_stats",
                "description": "Get statistics about your knowledge graph: node count, connectivity, top concepts.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "result": {"tools": tools},
        }

    def _handle_list_resources(self, request_id: str, jsonrpc: str) -> dict[str, Any]:
        """List available resources."""
        resources = [
            {
                "uri": "second-brain://vault/index",
                "name": "Vault Index",
                "description": "List all notes in your Obsidian vault",
                "mimeType": "application/json",
            },
            {
                "uri": "second-brain://persona",
                "name": "Persona",
                "description": "Your instruction layer: values, tone, decision framework",
                "mimeType": "application/json",
            },
            {
                "uri": "second-brain://telemetry",
                "name": "Telemetry Summary",
                "description": "Your query patterns and thinking insights",
                "mimeType": "application/json",
            },
        ]

        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "result": {"resources": resources},
        }

    def _handle_tool_call(
        self, request_id: str, jsonrpc: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle tool call."""
        tool_name = params.get("name")
        tool_input = params.get("arguments", {})

        result = None

        if tool_name == "ask":
            result = self.server.tool_ask(
                query=tool_input.get("query", ""),
                budget_tokens=tool_input.get("budget_tokens", 100000),
            )
        elif tool_name == "reflect":
            result = self.server.tool_reflect()
        elif tool_name == "search_notes":
            result = self.server.tool_search_notes(
                query=tool_input.get("query", ""),
                top_k=tool_input.get("top_k", 10),
            )
        elif tool_name == "get_connections":
            result = self.server.tool_get_connections(
                concept=tool_input.get("concept", "")
            )
        elif tool_name == "graph_stats":
            result = self.server.tool_graph_stats()
        else:
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                },
            }

        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "result": result,
        }

    def _handle_resource_read(
        self, request_id: str, jsonrpc: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle resource read."""
        uri = params.get("uri")

        result = None

        if uri == "second-brain://vault/index":
            result = self.server.resource_vault_index()
        elif uri == "second-brain://persona":
            result = self.server.resource_persona()
        elif uri == "second-brain://telemetry":
            result = self.server.resource_telemetry_summary()
        else:
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Resource not found: {uri}",
                },
            }

        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result, indent=2),
                    }
                ]
            },
        }


def main():
    """Main entry point for MCP server."""
    server = SecondBrainMCPServer()
    protocol = MCPProtocol(server)

    # Read requests from stdin, write responses to stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = protocol.handle_request(request)
            print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
