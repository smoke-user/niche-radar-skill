# Scoring Methodology

## Disruption Score Formula

```
disruption_score = (
    demand_signal       * 0.30 +   # Google Trends normalized interest
    forum_activity      * 0.20 +   # Reddit/HN/forum post count
    ad_gap              * 0.15 +   # 100 - ad_count_in_SERP (less ads = bigger gap)
    competitor_weakness  * 0.20 +  # 100 - normalized_competitor_traffic
    trend_direction     * 0.15     # Rising=100, Stable=60, Declining=20
)
```

## Signal Sources

| Signal | How to collect | Normalization |
|---|---|---|
| demand_signal | Google Trends interest_over_time | Raw 0-100 from Trends |
| forum_activity | Count Reddit posts with keyword (last 12mo) | log10(count) * 25, cap 100 |
| ad_gap | Count ads in top-10 SERP | 100 - (ad_count * 12.5), floor 0 |
| competitor_weakness | Highest competitor traffic estimate | Inverse: low traffic = high score |
| trend_direction | Google Trends slope over 12mo | Rising=100, Stable=60, Declining=20 |

## Market Color Classification

| Color | Score Range | Meaning |
|---|---|---|
| 🟢 Green | 70-100 | High demand, low competition — BUILD |
| 🟡 Yellow | 40-69 | Moderate — needs differentiation |
| 🔴 Red | 0-39 | Saturated or declining — AVOID |

## Competitor Traffic Tiers

| Tier | Monthly visits (est.) | Score impact |
|---|---|---|
| Tiny | < 1K | competitor_weakness = 90 |
| Small | 1K-10K | competitor_weakness = 70 |
| Medium | 10K-100K | competitor_weakness = 40 |
| Large | 100K-1M | competitor_weakness = 15 |
| Massive | > 1M | competitor_weakness = 5 |
