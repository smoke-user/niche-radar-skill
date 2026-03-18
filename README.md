# 🎯 Niche Radar

AI-powered pipeline to discover underserved market niches. Scores keywords by demand, competition, and competitor traffic using free data sources. No API keys required.

## Structure

```
niche-radar-skill/
├── SKILL.md                  ← AI agent instructions (skill format)
├── README.md                 ← This file
├── scripts/
│   ├── check_traffic.py      ← Competitor traffic estimation (free signals)
│   ├── expand_keywords.py    ← Keyword expansion via Google Autocomplete
│   ├── score_niche.py        ← SERP + traffic → Disruption Score (0-100)
│   └── rank_niches.py        ← Pipeline orchestrator + markdown report
└── references/
    ├── scoring.md            ← Disruption Score formula
    ├── traffic_signals.md    ← 10 free traffic estimation signals
    ├── idea_validation.md    ← Weighted idea scorer (11 criteria)
    └── competitor_db.md      ← 40+ competitors across 4 niches
```

## Quick Start

```bash
pip install requests beautifulsoup4 lxml

# Full pipeline
python scripts/rank_niches.py --seed "vibe coding testing" --depth 2

# Check a competitor's traffic
python scripts/check_traffic.py --domain "problemsifter.com"

# Score a single niche
python scripts/score_niche.py --keyword "AI code security"
```

## Pipeline

```
SEED → EXPAND → VALIDATE → SCORE → RANK → DECIDE
 (1)     (2)       (3)       (4)     (5)     (6)
```

1. **Seed** — provide 1-3 keywords or domains
2. **Expand** — generates 20-50 related keywords via Google Autocomplete
3. **Validate** — keeps only Stable/Rising trends
4. **Score** — SERP analysis + competitor traffic → Disruption Score
5. **Rank** — sorted Green/Yellow/Red report with competitor data
6. **Decide** — manual: weighted idea scorer + Weekend Test

## Usage with AI Agents

Add the contents of `SKILL.md` to your agent's system prompt or custom instructions. The scripts are called as standard CLI commands.

## API Keys

None required. All scripts use free, public data sources only.

## License

See [LICENSE](LICENSE).
