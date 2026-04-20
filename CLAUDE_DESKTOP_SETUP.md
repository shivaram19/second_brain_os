# Claude Desktop Integration

Connect your Second Brain OS to Claude Desktop as an MCP server.

## Setup (2 minutes)

### 1. Find Claude Desktop Config Location

Claude Desktop stores its configuration at:
```
~/.claude/claude_desktop_config.json
```

### 2. Add Second Brain OS Server

Edit `~/.claude/claude_desktop_config.json` and add:

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

**Important**: Adjust paths if your project is in a different location.

### 3. Verify Your Vault is Ingested

```bash
cd ~/Developer/second_brain_os
source venv/bin/activate
brainos ingest
```

This must complete successfully before Claude can query it.

### 4. Restart Claude Desktop

Close and reopen Claude Desktop. You should see a new "second-brain-os" option in the MCP servers section.

## Using in Claude Desktop

Once connected, Claude has access to these tools:

### `ask` - Query Your Knowledge
Searches your vault with hybrid retrieval (semantic + graph) and returns packed context.

```
Claude: ask "How does systems thinking relate to effective altruism?"
↓
Returns: 3-layer context
  - Instruction layer: your persona/values
  - Knowledge layer: relevant facts from vault
  - Tool layer: available capabilities
↓
Claude: Reasons over the context to answer you
```

### `reflect` - Self-Knowledge
Analyzes your knowledge graph for insights.

```
Claude: reflect
↓
Returns:
  - Core concepts (most connected ideas)
  - Blindspots (isolated concepts)
  - Suggested connections (where to add links)
  - Thinking patterns (what you query about)
```

### `search_notes` - Find Notes
Search for specific notes by keyword.

```
Claude: search_notes "effective altruism"
↓
Returns: Matching notes with previews
```

### `get_connections` - Explore Graph
Find related concepts in your knowledge graph.

```
Claude: get_connections "Systems Thinking"
↓
Returns: Connected concepts, network statistics
```

### `graph_stats` - Topology Analysis
Get overview of your knowledge structure.

```
Claude: graph_stats
↓
Returns: Total concepts, connections, density, top concepts
```

## Resources (Read-Only)

Claude can also read these resources:

- **Vault Index** - List of all notes
- **Persona** - Your instruction layer (values, tone, framework)
- **Telemetry** - Your query patterns and insights

## Token Usage

This MCP integration **minimizes token usage**:

- Without MCP: You dump entire vault into context (~100k tokens per query) = expensive
- With MCP: Claude calls `ask` tool, gets only relevant facts (~10-15k tokens) = efficient

## Example Conversation

```
You: "Based on my notes, what's my core thinking framework?"

Claude: [calls ask tool with your question]
Second Brain: [retrieves relevant concepts from vault]
Claude: "Based on your knowledge, your core framework involves:
  - Systems Thinking (15 connections - most central)
  - Effective Altruism (13 connections)
  - Causal Models (12 connections)

  These three form the foundation. You also think about
  Cause Prioritization and Long-term Thinking as applications..."

[Only used ~12k tokens for intelligent, grounded answer]
```

## Troubleshooting

### "Tool not found" error
- Make sure you ran `brainos ingest` successfully
- Restart Claude Desktop
- Check that PYTHONPATH is set correctly in config

### Slow responses
- First query downloads embeddings model (2-3 min one-time)
- Subsequent queries are instant (~150ms)
- Vault size affects speed; 100+ notes is normal

### "Vault not found" error
- Check `config/paths.yaml` has correct vault path
- Make sure vault exists at that path
- Run `brainos ingest` to verify

## Updating Configuration

If you change your vault location or settings:

1. Update `config/paths.yaml`
2. Restart Claude Desktop
3. Run `brainos ingest` again

## Security Notes

- MCP server runs locally on your Mac
- No data sent to external services (except embeddings model download, first-time only)
- All queries stay on your machine
- You control what Claude sees (only what's in your vault)

## Next: Test It

1. Open Claude Desktop
2. Make sure Second Brain OS shows as connected in settings
3. Ask: "What are my core concepts?"
4. Claude will call your MCP tools and answer based on your real knowledge

---

**Now your Second Brain is Claude's UI. No token waste, intelligent retrieval, complete context.**
