# Idea Validation Model

## Weighted Scoring (11 criteria, 95 max)

Derived from real niche-hunting session scoring 30+ ideas across AdTech, Crypto, AI/Dev Tools, GEO, and Vertical SaaS.

### Founder Fit (40% of total)

| Criterion | Weight | What to assess |
|---|---|---|
| Transferable Skills | ×1.5 | How well do your existing skills apply? (not just "I can code") |
| Existing Assets | ×1.0 | Can you reuse existing projects/code/data? (Worldsearch→Niche Radar, Solgemai→Gem Scorer) |
| Dog-fooding | ×1.0 | Would YOU use this product daily? Are you the target user? |
| Network Access | ×0.5 | Can you reach first 10 users without ads? (Telegram groups, Discord, Twitter) |

### Market Reality (35% of total)

| Criterion | Weight | What to assess |
|---|---|---|
| Market Validation | ×1.0 | How many competitors exist? (0=risky no demand, 5+=proven money, 15+=hot market) |
| Willingness to Pay | ×1.0 | Will people pay $20+/mo? Check: existing paid tools in adjacent space |
| Market Timing | ×1.0 | Is the wave NOW? (vibecoding=10, SEO=5, RSS readers=2) |
| Pain Frequency | ×0.5 | Daily pain > monthly pain > yearly pain |

### Execution Reality (25% of total)

| Criterion | Weight | What to assess |
|---|---|---|
| MVP Speed | ×1.0 | Can you ship MVP in 1 weekend? (1=impossible, 10=have code ready) |
| Budget Fit | ×0.5 | Runs on ≤$100/mo? (VPS + domain + API costs) |
| Virality | ×0.5 | Can product spread without paid ads? (public pages, embeds, share buttons) |

## Kill Filters

Apply BEFORE scoring. If ANY filter fails → idea is dead:

```
if budget_fit < 3: KILL "exceeds $100/mo"
if mvp_speed < 2: KILL "MVP > 3 months"
if (domain_expertise < 2 AND network < 2): KILL "no expertise + no access"
if market_validation < 2: KILL "no competitors = no proven demand"
if (wtp < 3 AND timing < 5): KILL "no money + bad timing"
```

## Competitive Analysis Framework

For each top-3 idea, research and fill:

### Direct Competitors Table

| Product | URL | Price | Target | Weakness |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### Key Questions

1. **How many direct competitors?** (0=green, 1-5=yellow, 10+=red)
2. **What's their traffic?** Run `check_traffic.py` on each
3. **What gap do they ALL miss?** (This is your angle)
4. **Is the name taken?** Check domain + app store + trademark
5. **Are competitors funded?** (VC-backed = harder to compete)

### Known Competitor Databases

Maintained in [competitor_db.md](competitor_db.md).

## Real-World Validation Results

### What Worked

| Idea | Score | Why it scored high |
|---|---|---|
| Solana Gem Scorer API | 80.5% | Existing Solgemai codebase (ClickHouse+ML+RugCheck) |
| Niche Radar | 80.0% | Existing Worldsearch (Scanner+Validator+Ranker) |
| Vibe QA | 75.3% | 0 competitors for vibecoder QA, explosive market |

### What Failed

| Idea | Score | Why it failed |
|---|---|---|
| Campaign Pre-Launch Checker | 84.4% | Real users said "we have everything in ad dashboards" |
| Am I In AI? | 68.4% | 15+ competitors appeared in <18 months |
| Freelancer Invoice CRM | — | Kill filter: red ocean (FreshBooks, Wave, Invoice Ninja) |

### Key Insight

> **High founder-fit score ≠ market validation.**
> Campaign Checker scored HIGHEST (84.4%) but was invalidated by 1 user interview.
> Always validate with real humans BEFORE building.
