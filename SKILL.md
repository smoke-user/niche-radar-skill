---
name: niche-radar
description: Systematic niche discovery and validation pipeline for finding green-market opportunities for pet projects and microSaaS. Use when the user mentions "find a niche", "market research", "idea validation", "green market", "blue ocean", "competitor analysis", "niche finder", or wants to evaluate whether a market is too crowded. Runs a 5-stage pipeline — Seed → Expand → Validate (Trends) → Score (SERP + Traffic) → Rank.
---

# Niche Radar

Systematic pipeline to discover and validate underserved market niches. Combines automated SERP/traffic analysis with manual validation steps learned from real niche-hunting sessions.

## Pipeline Overview

```
SEED → EXPAND → VALIDATE → SCORE → RANK → DECIDE
 (1)     (2)       (3)       (4)     (5)     (6)
```

| Stage | Script / Action | What it does |
|---|---|---|
| 1. Seed | Manual / AI | User provides 1-3 seed keywords or domains |
| 2. Expand | `scripts/expand_keywords.py` | Generates 20-50 keywords via Google Autocomplete |
| 3. Validate | Google Trends (manual or pytrends) | Keeps only Stable/Rising keywords |
| 4. Score | `scripts/score_niche.py` | SERP analysis + competitor traffic → Disruption Score |
| 5. Rank | `scripts/rank_niches.py` | Aggregates signals → sorted Green/Yellow/Red report |
| 6. Decide | Manual: Idea Scorer + Weekend Test | Weighted scoring + gut-check (see below) |

## How to Run

### Prerequisites

```bash
pip install requests beautifulsoup4 lxml
```

No API keys required. All scripts use free, public data sources.

### Quick Start

```bash
# Full pipeline from seeds
python scripts/rank_niches.py --seed "vibe coding testing" --depth 2

# Check single competitor's traffic
python scripts/check_traffic.py --domain "problemsifter.com"

# Score single niche keyword
python scripts/score_niche.py --keyword "AI code security scanner"
```

### Stage-by-stage

```bash
python scripts/expand_keywords.py --seed "AI code security" --out .tmp/keywords.json
python scripts/score_niche.py --input .tmp/keywords.json --out .tmp/scored.json
python scripts/rank_niches.py --input .tmp/scored.json
```

## Disruption Score (0-100)

```
disruption_score = (
    demand_signal       * 0.30 +   # Google Trends interest (0-100)
    forum_activity      * 0.20 +   # Reddit/HN/forum mentions
    (100 - ad_density)  * 0.15 +   # Low ads = room for you
    market_validation   * 0.20 +   # Many competitors = proven money
    trend_direction     * 0.15     # Rising=100 > Stable=60 > Declining=20
)
```

| Color | Score | Meaning |
|---|---|---|
| 🟢 Green | 70-100 | Low competition, high demand — **BUILD** |
| 🟡 Yellow | 40-69 | Moderate — needs differentiation |
| 🔴 Red | 0-39 | Saturated or declining — **AVOID** |

## Traffic Checker

`scripts/check_traffic.py` estimates competitor traffic from **free signals only**:

| Signal | Source | Accuracy |
|---|---|---|
| Indexed pages | `site:domain` Google query | ★★★ |
| Homepage HTML | OG tags, analytics, tech stack | ★★ |
| Wayback snapshots | Wayback CDX API | ★★ |
| Brand search trend | Google Trends | ★★★ |
| GitHub stars / PH upvotes | If applicable | ★★★★ |

Output: tier classification (Tiny <1K, Small 1K-10K, Medium 10K-100K, Large 100K-1M+).

## Stage 6: Manual Validation (CRITICAL)

> The pipeline gives you data. This stage gives you **conviction**.

After ranking, apply these two manual filters from [references/idea_validation.md](references/idea_validation.md):

### Idea Scorer (11 weighted criteria)

Score each surviving idea 1-10 on:

| Category (weight) | Criteria |
|---|---|
| **Founder Fit (40%)** | Transferable skills (×1.5), Existing assets/code (×1.0), Dog-fooding — would YOU use it? (×1.0), Network access to first 10 users (×0.5) |
| **Market Reality (35%)** | Competition gap (×1.0), Willingness to pay (×1.0), Market timing — is the wave NOW? (×1.0), Pain frequency (×0.5) |
| **Execution (25%)** | MVP in 1 weekend? (×1.0), Budget fit ≤$100/mo (×0.5), Virality potential (×0.5) |

### Kill Filters (binary)

Eliminate ideas that fail ANY:
- Budget > $100/mo to run
- MVP > 3 months
- Zero domain expertise AND zero network
- Competition gap < 2/10 (absolute red ocean)
- WTP < 3 AND market timing < 5

### Weekend Test (5 questions, answer 1-10)

| Question | Your score |
|---|---|
| Does the idea *excite* you? | ___ |
| Can you build MVP this weekend? | ___ |
| Do you know 5 people to show it Monday? | ___ |
| Would YOU use this product daily? | ___ |
| Do you have code/data to reuse? | ___ |

> All ≥ 7 → **Start today**. Any < 5 → try next idea.

## Red Flags Checklist

When analyzing a competitor or reference product, check for:

| Signal | What it means |
|---|---|
| No ad traffic at all | Either organic-only or very early stage |
| Solo founder (ИП/LLC) | Indie project, not VC-backed (can be advantage) |
| No public case studies | Product may be pre-PMF |
| No G2/ProductHunt reviews | Not validated by market yet |
| **0 competitors** | 🔴 Possibly no demand. Validate carefully |
| **15+ competitors** | 🟢 Proven demand, money flows here. Find your angle |
| Name already taken | Critical — check trademark + domain + app stores |

## Reference Files

- **Scoring methodology**: See [references/scoring.md](references/scoring.md) — detailed formula breakdown
- **Traffic estimation signals**: See [references/traffic_signals.md](references/traffic_signals.md) — 10 free + paid signals
- **Idea validation model**: See [references/idea_validation.md](references/idea_validation.md) — weighted scorer, kill filters, competitive analysis framework
- **Competitor database**: See [references/competitor_db.md](references/competitor_db.md) — known competitors per niche (Niche Finder, Vibe QA, VibeSafe, GEO tools)

## Key Learnings (from real niche-hunting sessions)

1. **AdTech trap**: Ideas in your domain expertise score highest BUT validate with real users. "Campaign Pre-Launch Checker" scored 84% yet real buyers said "everything is already in the ad dashboard" → invalidated.
2. **Existing code = unfair advantage**: Top ideas are often productizations of projects you already built. Check your repos before ideating from scratch.
3. **15+ competitors = GREEN market**: Many competitors prove demand and money flow. Zero competitors is the real risk — it may mean no market exists. Your job is to find a differentiation angle, not an empty field.
4. **Dog-fooding → conviction**: If you're literally experiencing the pain right now (searching for a niche), that's the strongest signal.
5. **Traffic check reveals weak competitors**: A competitor with Tiny traffic (<1K) = validated demand + poor execution = opportunity for you.

## Important Notes

- Rate-limit all HTTP requests (1-2 sec between calls) to avoid blocks
- Traffic estimates are **directional** (tiers), not exact numbers
- Google may block automated queries — implement retry with backoff
- For accurate traffic: integrate SimilarWeb API ($$$) or SEMrush ($99+/mo)
