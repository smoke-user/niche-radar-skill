# Traffic Estimation Signals

Free methods to estimate competitor website traffic without paid APIs.

## Signal Matrix

| # | Signal | Source | Cost | Accuracy | How |
|---|---|---|---|---|---|
| 1 | **SERP keyword count** | Google Search | Free | ★★★ | `site:domain.com` → result count |
| 2 | **Backlink estimate** | Google Search | Free | ★★★ | `link:domain.com` or check referring pages |
| 3 | **Domain age** | WHOIS (python-whois) | Free | ★★ | Older = more established |
| 4 | **Tech stack** | HTML meta/headers | Free | ★★ | WordPress vs custom, analytics tags |
| 5 | **Social proof** | HTML meta tags | Free | ★★ | OG tags, Twitter cards, social links |
| 6 | **Chrome Web Store** | If extension | Free | ★★★★ | Exact user count visible |
| 7 | **GitHub stars** | GitHub API | Free | ★★★ | Direct proxy for dev-tool popularity |
| 8 | **Product Hunt upvotes** | PH page | Free | ★★ | Launch traction signal |
| 9 | **Google Trends brand** | Trends API | Free | ★★★ | Brand search volume = traffic proxy |
| 10 | **Wayback snapshots** | Wayback CDX API | Free | ★★ | More snapshots = more traffic historically |

## Traffic Tier Estimation Logic

```python
def estimate_tier(signals: dict) -> str:
    score = 0
    
    # SERP indexed pages
    indexed = signals.get("indexed_pages", 0)
    if indexed > 10000: score += 30
    elif indexed > 1000: score += 20
    elif indexed > 100: score += 10
    
    # Domain age (years)
    age = signals.get("domain_age_years", 0)
    if age > 5: score += 20
    elif age > 2: score += 10
    elif age > 1: score += 5
    
    # Brand search volume (Google Trends 0-100)
    brand_trend = signals.get("brand_trend", 0)
    if brand_trend > 50: score += 30
    elif brand_trend > 20: score += 15
    elif brand_trend > 5: score += 5
    
    # Social signals
    has_twitter = signals.get("has_twitter", False)
    has_og = signals.get("has_og_tags", False)
    if has_twitter: score += 5
    if has_og: score += 5
    
    # Tech investment
    is_custom = signals.get("is_custom_build", False)
    has_analytics = signals.get("has_analytics", False)
    if is_custom: score += 5
    if has_analytics: score += 5
    
    # Classify
    if score >= 70: return "Large (100K-1M+)"
    if score >= 45: return "Medium (10K-100K)"
    if score >= 25: return "Small (1K-10K)"
    return "Tiny (<1K)"
```

## Paid API Alternatives (if budget allows)

| Service | Cost | Accuracy |
|---|---|---|
| SimilarWeb API | $$$$ (enterprise) | ★★★★★ |
| SEMrush Traffic Analytics | $99+/мес | ★★★★ |
| Ahrefs Traffic Estimate | $99+/мес | ★★★★ |
| SEO Review Tools API | ~$50/мес | ★★★ |
| Apify Traffic Estimator | Pay-per-run | ★★★ |
