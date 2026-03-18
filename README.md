# 🎯 Niche Radar

AI-powered pipeline to discover underserved market niches. Scores keywords by demand, competition, and competitor traffic using free data sources. No API keys required.

## Two Ways to Use

### 1. MCP Server (for AI agents)

Works with Claude Desktop, Cursor, Cline, Windsurf, OpenClaw, and any MCP-compatible client.

**Local (stdio):**
```json
{
  "mcpServers": {
    "niche-radar": {
      "command": "python",
      "args": ["/path/to/niche-radar-skill/mcp_server.py"]
    }
  }
}
```

**Remote server (SSE):**
```bash
# On your server
git clone https://github.com/smoke-user/niche-radar-skill.git
cd niche-radar-skill
pip install -r requirements.txt
python mcp_server.py --sse --port 8080
```

**Available MCP tools:**

| Tool | What it does |
|---|---|
| `check_traffic` | Estimate competitor traffic from free signals |
| `score_niche` | SERP + traffic → Disruption Score (0-100) |
| `expand_keywords` | Seed → 20-50 related keywords via Google Autocomplete |
| `run_pipeline` | Full pipeline: expand → score → rank → markdown report |

### 2. CLI (standalone scripts)

```bash
pip install -r requirements.txt

# Full pipeline
python scripts/rank_niches.py --seed "vibe coding testing" --depth 2

# Check a competitor's traffic
python scripts/check_traffic.py --domain "problemsifter.com"

# Score a single niche
python scripts/score_niche.py --keyword "AI code security"
```

## Structure

```
niche-radar-skill/
├── mcp_server.py             ← MCP server (4 tools, stdio + SSE)
├── requirements.txt          ← Python dependencies
├── SKILL.md                  ← AI agent instructions
├── scripts/
│   ├── check_traffic.py      ← Competitor traffic estimation
│   ├── expand_keywords.py    ← Keyword expansion
│   ├── score_niche.py        ← SERP + traffic → Disruption Score
│   └── rank_niches.py        ← Pipeline orchestrator + report
└── references/
    ├── scoring.md            ← Disruption Score formula
    ├── traffic_signals.md    ← 10 free traffic estimation signals
    ├── idea_validation.md    ← Weighted idea scorer (11 criteria)
    └── competitor_db.md      ← 40+ competitors across 4 niches
```

## Deploy to Server

```bash
# 1. Clone
git clone https://github.com/smoke-user/niche-radar-skill.git
cd niche-radar-skill

# 2. Install deps
pip install -r requirements.txt

# 3. Run MCP server
python mcp_server.py --sse --port 8080

# 4. Or run CLI directly
python scripts/rank_niches.py --seed "your idea here"
```

## API Keys

None required. All data comes from free, public sources.

## License

See [LICENSE](LICENSE).
