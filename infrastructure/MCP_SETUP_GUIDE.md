# MCP Server Stack — Setup Guide
## Exocortex Infrastructure
## April 23, 2026

---

## What Changed

Two new servers added to the existing stack:

| Server | Port | What It Does | Why It Matters |
|--------|------|-------------|----------------|
| **ArXiv** | 8013 | Search, download, read research papers | Gives the agent the same research capability Opus uses. The agent can independently pull papers instead of waiting for briefings. |
| **DuckDuckGo** | 8014 | Web search, no API key needed | Gives the agent web search capability for geopolitical, technical, and current-events research. |

Everything else is carried over from the existing docker-compose with two removals:
- **Filesystem** — removed for security. The agent shouldn't have host filesystem access.
- **SQLite** — removed. Agent Zero uses FAISS, not SQLite.

## How To Deploy

### Option A: Replace the existing docker-compose
```powershell
# Stop current MCP stack
cd D:\Vibecode\Agent-Zero
docker-compose down

# Copy new file
copy Exocortex\infrastructure\docker-compose-mcp.yml docker-compose.yml

# Update the Obsidian vault path in docker-compose.yml
# (line with "UPDATE THIS PATH")

# Start new stack
docker-compose up -d
```

### Option B: Run alongside existing stack
```powershell
# Just start the new servers (they use different ports)
cd D:\Vibecode\Agent-Zero\Exocortex\infrastructure
docker-compose -f docker-compose-mcp.yml up -d mcp-arxiv mcp-duckduckgo
```

### Verify
```powershell
# Check all services are running
docker-compose ps

# Test ArXiv
curl http://localhost:8013/sse

# Test DuckDuckGo
curl http://localhost:8014/sse
```

## Agent Zero MCP Configuration

The agent connects to MCP servers via its settings. In Agent Zero's MCP configuration, add:

```json
{
  "mcp_servers": {
    "context7": {
      "url": "http://host.docker.internal:8001/sse",
      "transport": "sse"
    },
    "fetch": {
      "url": "http://host.docker.internal:8002/sse",
      "transport": "sse"
    },
    "memory": {
      "url": "http://host.docker.internal:8003/sse",
      "transport": "sse"
    },
    "sequential-thinking": {
      "url": "http://host.docker.internal:8004/sse",
      "transport": "sse"
    },
    "wikipedia": {
      "url": "http://host.docker.internal:8005/sse",
      "transport": "sse"
    },
    "markitdown": {
      "url": "http://host.docker.internal:8008/sse",
      "transport": "sse"
    },
    "youtube": {
      "url": "http://host.docker.internal:8009/sse",
      "transport": "sse"
    },
    "deepwiki": {
      "url": "http://host.docker.internal:8010/sse",
      "transport": "sse"
    },
    "playwright": {
      "url": "http://host.docker.internal:8011/sse",
      "transport": "sse"
    },
    "obsidian": {
      "url": "http://host.docker.internal:8012/sse",
      "transport": "sse"
    },
    "arxiv": {
      "url": "http://host.docker.internal:8013/sse",
      "transport": "sse"
    },
    "duckduckgo": {
      "url": "http://host.docker.internal:8014/sse",
      "transport": "sse"
    }
  }
}
```

**Note:** The exact config format depends on how Agent Zero V17 handles MCP connections. Check `/a0/usr/settings.json` or the MCP plugin configuration for the correct key names. The URLs above use `host.docker.internal` which resolves to the host machine from inside the Docker container.

## What This Enables

With ArXiv + DuckDuckGo, the agent can:

1. **Research independently.** Instead of waiting for Opus to read papers and brief it, the agent can search arXiv, download papers, and read them itself. This changes the team dynamic — the agent becomes a research participant, not just a research consumer.

2. **Verify its own claims.** The epistemic integrity layer catches ungrounded claims. With web search, the agent can ground them. "GDP growth was 3.2%" → search → verify or correct. This directly addresses the confabulation pattern we documented.

3. **Stay current.** The Qwen3.6-27B has a training cutoff. DuckDuckGo search gives it access to current events — critical for the geopolitical investigation workloads.

4. **Access the same knowledge graph as Opus.** The memory server (port 8003) is the shared knowledge graph. If both the agent and Opus write to it, it becomes a true shared memory between the team.

## Security Notes

- **No host filesystem access.** The filesystem MCP server is deliberately excluded.
- **No git push capability.** GitHub MCP is not included.
- **No API keys required.** DuckDuckGo and ArXiv both work without authentication.
- **ArXiv papers are stored in a Docker volume** (`arxiv-papers`), not on the host filesystem.
- **Memory data is stored in a Docker volume** (`memory-data`), persisting across container restarts.

## Future Additions (require API keys)

| Server | What It Needs | What It Does |
|--------|--------------|--------------|
| Brave Search | `BRAVE_API_KEY` | Higher-quality web search results |
| Hugging Face | `HF_TOKEN` | Model/dataset lookup, paper search |
| Tavily | `TAVILY_API_TOKEN` | Search + intelligent web extraction |
| Exa | `EXA_API_KEY` | Semantic web search |

Add these when you want higher-quality search results. DuckDuckGo is the zero-config starting point.
