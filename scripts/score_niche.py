"""
Niche Scorer — SERP analysis + competitor traffic → Disruption Score.

Scoring formula (references/scoring.md):
  disruption_score = demand*0.30 + forum*0.20 + ad_gap*0.15 + weakness*0.20 + trend_dir*0.15

Google Trends is fetched automatically when no explicit trend_value is provided.
"""

import argparse
import json
import math
import os
import re
import sys
import time
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ pip install requests beautifulsoup4 lxml")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from check_traffic import check_traffic, clean_domain


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}
DELAY = 2.0


def fetch_trends(keyword: str) -> tuple[int, str]:
    """Fetch Google Trends interest for a keyword.

    Returns (value 0-100, direction: "rising"|"stable"|"declining"|"unknown").
    Falls back to (50, "unknown") on any error.
    """
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-US", tz=360, timeout=(5, 20), retries=1, backoff_factor=0.5)
        pt.build_payload([keyword], timeframe="today 12-m")
        df = pt.interest_over_time()
        if df is None or df.empty or keyword not in df.columns:
            return 50, "unknown"

        values = df[keyword].tolist()
        avg = int(sum(values) / len(values))

        # Direction: compare average of last 3 months to first 3 months
        direction = "stable"
        if len(values) >= 6:
            recent = sum(values[-3:]) / 3
            old = sum(values[:3]) / 3
            if old > 0:
                change = (recent - old) / old
                if change > 0.15:
                    direction = "rising"
                elif change < -0.15:
                    direction = "declining"
                else:
                    direction = "stable"
            elif recent > 5:
                direction = "rising"

        return avg, direction
    except Exception as e:
        print(f"  ⚠️  Trends fetch failed: {e}")
        return 50, "unknown"


def analyze_serp(keyword: str) -> dict:
    """Analyze Google SERP for a keyword."""
    result = {
        "keyword": keyword,
        "total_results": 0,
        "ad_count": 0,
        "organic_domains": [],
        "has_featured_snippet": False,
        "has_people_also_ask": False,
    }

    url = f"https://www.google.com/search?q={requests.utils.quote(keyword)}&num=10&hl=en"
    time.sleep(DELAY)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            result["error"] = f"HTTP {r.status_code}"
            return result
    except Exception as e:
        result["error"] = str(e)
        return result

    soup = BeautifulSoup(r.text, "lxml")

    # Total results
    stats = soup.find("div", id="result-stats")
    if stats:
        match = re.search(r"([\d,]+)\s+results", stats.text)
        if match:
            result["total_results"] = int(match.group(1).replace(",", ""))

    # Count ads
    ad_markers = soup.find_all("span", string=re.compile(r"^(Sponsored|Ad)$", re.I))
    result["ad_count"] = len(ad_markers)
    ad_divs = soup.find_all("div", attrs={"data-text-ad": True})
    if ad_divs:
        result["ad_count"] = max(result["ad_count"], len(ad_divs))

    # Extract organic domains
    skip = {
        "google.com", "youtube.com", "facebook.com", "twitter.com",
        "instagram.com", "linkedin.com", "reddit.com", "wikipedia.org",
        "amazon.com", "gstatic.com", "googleapis.com",
    }
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("/url?") or href.startswith("https://"):
            match = re.search(r"(?:https?://)?(?:www\.)?([a-zA-Z0-9\-]+\.[a-zA-Z]{2,})", href)
            if match:
                domain = match.group(1)
                if domain not in skip and domain not in result["organic_domains"]:
                    result["organic_domains"].append(domain)
                    if len(result["organic_domains"]) >= 10:
                        break

    if soup.find("div", class_=re.compile(r"featured")):
        result["has_featured_snippet"] = True

    if soup.find("div", attrs={"data-sgrd": True}) or "People also ask" in r.text:
        result["has_people_also_ask"] = True

    return result


TIER_TO_SCORE = {
    "Tiny (<1K)": 90,
    "Small (1K-10K)": 70,
    "Medium (10K-100K)": 40,
    "Large (100K-1M+)": 15,
}


def score_niche(
    keyword: str,
    trend_value: int = 50,
    trend_direction: str = "stable",
    forum_mentions: int = 10,
    check_competitors: bool = True,
) -> dict:
    """Full scoring pipeline for a niche keyword.

    Google Trends data is fetched automatically when trend_value and
    trend_direction are at their defaults (50 / "stable"). Pass explicit
    values to skip auto-fetch.
    """
    print(f"\n🎯 Scoring niche: '{keyword}'")
    print("-" * 50)

    # Auto-fetch trends when caller uses defaults
    trends_source = "default"
    if trend_value == 50 and trend_direction == "stable":
        print("  📈 Fetching Google Trends...")
        fetched_value, fetched_direction = fetch_trends(keyword)
        if fetched_direction != "unknown":
            trend_value = fetched_value
            trend_direction = fetched_direction
            trends_source = "auto"
            print(f"     → {trend_value}/100, direction: {trend_direction}")
        else:
            print(f"     → Trends unavailable, using defaults")

    # SERP Analysis
    print("  📊 Analyzing SERP...")
    serp = analyze_serp(keyword)
    print(f"     → {serp['total_results']:,} results, {serp['ad_count']} ads, "
          f"{len(serp['organic_domains'])} competitors")

    # Traffic check for top 3 competitors
    competitor_scores = []
    if check_competitors and serp["organic_domains"]:
        top_3 = serp["organic_domains"][:3]
        print(f"  🔍 Checking traffic for: {', '.join(top_3)}")
        for domain in top_3:
            traffic = check_traffic(domain, verbose=False)
            tier_score = TIER_TO_SCORE.get(traffic["traffic_tier"], 50)
            competitor_scores.append({
                "domain": domain,
                "tier": traffic["traffic_tier"],
                "weakness_score": tier_score,
            })
            print(f"     → {domain}: {traffic['traffic_tier']}")

    # Disruption Score calculation (scoring.md formula)
    demand = trend_value  # 0-100

    forum_score = min(100, math.log10(max(1, forum_mentions)) * 25)

    ad_gap = max(0, 100 - serp["ad_count"] * 12.5)

    if competitor_scores:
        competitor_weakness = sum(c["weakness_score"] for c in competitor_scores) / len(competitor_scores)
    else:
        competitor_weakness = 80  # No competitors = green signal

    trend_map = {"rising": 100, "stable": 60, "declining": 20, "unknown": 50}
    trend_dir_score = trend_map.get(trend_direction.lower(), 50)

    disruption_score = round(
        demand * 0.30 +
        forum_score * 0.20 +
        ad_gap * 0.15 +
        competitor_weakness * 0.20 +
        trend_dir_score * 0.15,
        1,
    )

    if disruption_score >= 70:
        color = "🟢 GREEN"
    elif disruption_score >= 40:
        color = "🟡 YELLOW"
    else:
        color = "🔴 RED"

    print(f"\n  📊 Disruption Score: {disruption_score}/100 {color}")
    print(f"     Breakdown: demand={demand:.0f} forum={forum_score:.0f} "
          f"ad_gap={ad_gap:.0f} weakness={competitor_weakness:.0f} "
          f"trend={trend_dir_score:.0f} (trends_source={trends_source})")

    return {
        "keyword": keyword,
        "disruption_score": disruption_score,
        "color": color,
        "breakdown": {
            "demand_signal": round(demand, 1),
            "forum_activity": round(forum_score, 1),
            "ad_gap": round(ad_gap, 1),
            "competitor_weakness": round(competitor_weakness, 1),
            "trend_direction": trend_dir_score,
            "trends_source": trends_source,
        },
        "serp": {
            "total_results": serp["total_results"],
            "ad_count": serp["ad_count"],
            "competitor_count": len(serp["organic_domains"]),
            "top_domains": serp["organic_domains"][:5],
        },
        "competitors": competitor_scores,
    }


def main():
    parser = argparse.ArgumentParser(description="Score a niche keyword")
    parser.add_argument("--keyword", "-k", help="Single keyword to score")
    parser.add_argument("--input", "-i", help="JSON file with keywords (from expand_keywords)")
    parser.add_argument("--out", "-o", help="Output JSON file")
    parser.add_argument("--no-traffic", action="store_true", help="Skip competitor traffic checks")
    args = parser.parse_args()

    results = []

    if args.keyword:
        r = score_niche(args.keyword, check_competitors=not args.no_traffic)
        results.append(r)
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            keywords = json.load(f)
        for kw_data in keywords:
            kw = kw_data if isinstance(kw_data, str) else kw_data.get("keyword", "")
            if kw:
                r = score_niche(kw, check_competitors=not args.no_traffic)
                results.append(r)
    else:
        print("Use --keyword or --input")
        sys.exit(1)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Saved {len(results)} scores to {args.out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🧪 Self-test: scoring 'vibe coding testing tool' (no-traffic mode)")
        result = score_niche(
            "vibe coding testing tool",
            trend_value=60,
            trend_direction="rising",
            check_competitors=False,
        )
        print(f"\n✅ Self-test passed: {result['disruption_score']}/100 {result['color']}")
    else:
        main()
