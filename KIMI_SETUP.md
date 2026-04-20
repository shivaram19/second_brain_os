# Kimi CLI Integration

Connect your Second Brain OS to [Kimi Code CLI](https://github.com/MoonshotAI/Kimi-CLI) as an MCP server.

## Quick Setup (2 minutes)

### 1. Add the MCP Server

From your project directory:

```bash
cd ~/Developer/second_brain_os
source venv/bin/activate
kimi mcp add --transport stdio second-brain-os -- python -m brainos.mcp_servers.run_server
```

Or manually edit `~/.kimi/mcp.json`:

```json
{
  "mcpServers": {
    "second-brain-os": {
      "command": "python",
      "args": [
        "-m",
        "brainos.mcp_servers.run_server"
      ],
      "cwd": "/Users/shivaramgoud/Developer/second_brain_os",
      "env": {
        "PYTHONPATH": "/Users/shivaramgoud/Developer/second_brain_os"
      }
    }
  }
}
```

### 2. Verify Your Vault is Ingested

```bash
cd ~/Developer/second_brain_os
source venv/bin/activate
brainos ingest
```

This must complete successfully before Kimi can query it.

### 3. Test It

Start a Kimi session and ask:

```
What are my core concepts based on my notes?
```

Kimi will call your MCP tools and answer based on your real knowledge.

---

## Using in Kimi CLI

Once connected, Kimi has access to these tools:

### `ask` — Query Your Knowledge
Searches your vault with hybrid retrieval (semantic + graph) and returns packed context.

```
You: How does systems thinking relate to effective altruism?
Kimi: [calls ask tool]
Second Brain: [retrieves relevant concepts]
Kimi: "Based on your knowledge, your core framework involves..."
```

### `reflect` — Self-Knowledge
Analyzes your knowledge graph for insights.

```
You: Reflect on my knowledge
Kimi: [calls reflect tool]
Returns:
  - Core concepts (most connected ideas)
  - Blindspots (isolated concepts)
  - Suggested connections
  - Thinking patterns
```

### `search_notes` — Find Notes
Search for specific notes by keyword.

### `get_connections` — Explore Graph
Find related concepts in your knowledge graph.

### `graph_stats` — Topology Analysis
Get overview of your knowledge structure.

---

## Token Efficiency

This MCP integration **minimizes token usage**:

| Without MCP | With MCP |
|-------------|----------|
| You paste entire vault (~100k tokens) | Kimi calls `ask` tool |
| Kimi reads raw data | Gets only relevant facts |
| ~$1-5 per query | ~$0.01-0.05 per query |

**100x more efficient. Same intelligence.**

---

## Alternative: Moonshot AI LLM Backend

Second Brain OS supports Moonshot AI (Kimi) as an alternative LLM provider to Anthropic.

Set your API key:

```bash
export MOONSHOT_API_KEY="your-api-key"
```

The ResearchAgent and DraftingAgent will use Moonshot's `moonshot-v1-128k` model
when the Anthropic client is unavailable or when explicitly configured.

---

## Troubleshooting

### "Tool not found" error
- Make sure you ran `brainos ingest` successfully
- Check that `PYTHONPATH` is set correctly in MCP config
- Restart Kimi CLI

### Slow responses
- First query downloads embeddings model (2-3 min one-time)
- Subsequent queries are instant (~150ms)

### "Vault not found" error
- Check `config/paths.yaml` has correct vault path
- Make sure vault exists at that path
- Run `brainos ingest` to verify

---

**Now your Second Brain is Kimi's UI. No token waste. Intelligent retrieval. Complete context.**
