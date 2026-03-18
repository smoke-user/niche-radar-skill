"""
/* LOGIC CHECK:
- Orchestrator: runs full pipeline or consumes pre-scored data
- Modes: (A) full pipeline from seeds, (B) rank pre-scored JSON
- Generates markdown report sorted by disruption_score
- Groups into Green/Yellow/Red zones
- Includes competitor traffic data in output
*/

Niche Ranker — orchestrate pipeline and generate final report.
"""

import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def generate_report(scored: list[dict], seeds: list[str] = None) -> str:
    """Generate markdown report from scored niches."""
    lines = []
    lines.append("# 🎯 Niche Radar Report\n")
    lines.append(f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if seeds:
        lines.append(f"> **Seeds:** {', '.join(seeds)}")
    lines.append(f"> **Niches analyzed:** {len(scored)}\n")
    lines.append("---\n")

    # Sort by score descending
    scored.sort(key=lambda x: x.get("disruption_score", 0), reverse=True)

    # Group by color
    green = [s for s in scored if s.get("disruption_score", 0) >= 70]
    yellow = [s for s in scored if 40 <= s.get("disruption_score", 0) < 70]
    red = [s for s in scored if s.get("disruption_score", 0) < 40]

    # Summary bar
    lines.append("## 📊 Summary\n")
    lines.append(f"| Zone | Count | Meaning |")
    lines.append(f"|---|---|---|")
    lines.append(f"| 🟢 Green | {len(green)} | High demand, low competition — BUILD |")
    lines.append(f"| 🟡 Yellow | {len(yellow)} | Moderate — needs differentiation |")
    lines.append(f"| 🔴 Red | {len(red)} | Saturated or declining — AVOID |")
    lines.append("")

    def render_group(title: str, items: list[dict]):
        if not items:
            return
        lines.append(f"---\n")
        lines.append(f"## {title}\n")
        lines.append("| # | Keyword | Score | Ads | Competitors | Top Competitor | Traffic |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, item in enumerate(items, 1):
            kw = item.get("keyword", "?")
            score = item.get("disruption_score", 0)
            serp = item.get("serp", {})
            ads = serp.get("ad_count", "?")
            comp_count = serp.get("competitor_count", "?")
            top_domains = serp.get("top_domains", [])
            top_domain = top_domains[0] if top_domains else "—"

            # Top competitor traffic
            competitors = item.get("competitors", [])
            if competitors:
                top_traffic = competitors[0].get("tier", "?")
            else:
                top_traffic = "Unknown"

            lines.append(f"| {i} | **{kw}** | {score} | {ads} | {comp_count} | "
                        f"{top_domain} | {top_traffic} |")
        lines.append("")

        # Detailed breakdown for top 3
        for i, item in enumerate(items[:3], 1):
            kw = item.get("keyword", "?")
            score = item.get("disruption_score", 0)
            bd = item.get("breakdown", {})
            lines.append(f"### #{i}: {kw} ({score}/100)\n")
            lines.append("| Signal | Score | Weight |")
            lines.append("|---|---|---|")
            lines.append(f"| Demand (Trends) | {bd.get('demand_signal', '?')} | ×0.30 |")
            lines.append(f"| Forum Activity | {bd.get('forum_activity', '?')} | ×0.20 |")
            lines.append(f"| Ad Gap | {bd.get('ad_gap', '?')} | ×0.15 |")
            lines.append(f"| Competitor Weakness | {bd.get('competitor_weakness', '?')} | ×0.20 |")
            lines.append(f"| Trend Direction | {bd.get('trend_direction', '?')} | ×0.15 |")
            lines.append("")

            # Competitor details
            competitors = item.get("competitors", [])
            if competitors:
                lines.append("**Competitors traffic:**\n")
                lines.append("| Domain | Traffic Tier | Weakness Score |")
                lines.append("|---|---|---|")
                for c in competitors:
                    lines.append(f"| {c['domain']} | {c['tier']} | {c['weakness_score']} |")
                lines.append("")

    render_group("🟢 Green Zone (Score ≥ 70) — BUILD", green)
    render_group("🟡 Yellow Zone (Score 40-69) — DIFFERENTIATE", yellow)
    render_group("🔴 Red Zone (Score < 40) — AVOID", red)

    # Verdict
    if green:
        top = green[0]
        lines.append("---\n")
        lines.append("## 🏆 Verdict\n")
        lines.append(f"> **Top niche: {top['keyword']}** — Score {top['disruption_score']}/100")
        lines.append(f">")
        serp = top.get("serp", {})
        lines.append(f"> - {serp.get('ad_count', '?')} ads in SERP (low = opportunity)")
        lines.append(f"> - {serp.get('competitor_count', '?')} direct competitors")
        comps = top.get("competitors", [])
        if comps:
            lines.append(f"> - Top competitor traffic: {comps[0]['tier']}")
        lines.append(f">")
        lines.append(f"> **Next step:** Build an MVP and test with 5 potential users this weekend.")

    return "\n".join(lines)


def run_full_pipeline(seeds: list[str], depth: int = 2, max_kw: int = 20,
                      check_competitors: bool = True) -> str:
    """Run the complete pipeline: expand → score → rank → report."""
    from expand_keywords import expand_keywords
    from score_niche import score_niche

    print("=" * 60)
    print("🚀 Niche Radar — Full Pipeline")
    print("=" * 60)

    # Stage 1: Expand
    print(f"\n📌 Stage 1/3: Expanding seeds: {seeds}")
    keywords = expand_keywords(seeds, depth=depth, max_keywords=max_kw)
    print(f"   → {len(keywords)} keywords\n")

    # Stage 2: Score
    print(f"📌 Stage 2/3: Scoring {len(keywords)} niches...")
    scored = []
    for kw_data in keywords:
        kw = kw_data["keyword"] if isinstance(kw_data, dict) else kw_data
        try:
            result = score_niche(kw, check_competitors=check_competitors)
            scored.append(result)
        except Exception as e:
            print(f"  ❌ Failed to score '{kw}': {e}")

    # Stage 3: Rank and report
    print(f"\n📌 Stage 3/3: Ranking and generating report...")
    report = generate_report(scored, seeds)

    return report


def main():
    parser = argparse.ArgumentParser(description="Niche Radar — find green market opportunities")
    parser.add_argument("--seed", "-s", help="Comma-separated seed keywords for full pipeline")
    parser.add_argument("--input", "-i", help="Pre-scored JSON file to rank")
    parser.add_argument("--depth", "-d", type=int, default=2, help="Keyword expansion depth")
    parser.add_argument("--max", "-m", type=int, default=20, help="Max keywords to analyze")
    parser.add_argument("--out", "-o", default="niche_radar_report.md", help="Output report path")
    parser.add_argument("--no-traffic", action="store_true", help="Skip traffic checks (faster)")
    args = parser.parse_args()

    if args.input:
        # Mode B: rank pre-scored data
        with open(args.input, "r", encoding="utf-8") as f:
            scored = json.load(f)
        report = generate_report(scored)
    elif args.seed:
        # Mode A: full pipeline
        seeds = [s.strip() for s in args.seed.split(",")]
        report = run_full_pipeline(seeds, depth=args.depth, max_kw=args.max,
                                   check_competitors=not args.no_traffic)
    else:
        print("Use --seed for full pipeline or --input for pre-scored data")
        sys.exit(1)

    # Save report
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 Report saved to: {args.out}")
    print("✅ Done!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Self-test with mock data
        print("🧪 Self-test: generating report from mock data")
        mock = [
            {"keyword": "vibe coding tester", "disruption_score": 82, "color": "🟢 GREEN",
             "breakdown": {"demand_signal": 70, "forum_activity": 50, "ad_gap": 100,
                           "competitor_weakness": 80, "trend_direction": 100},
             "serp": {"total_results": 500, "ad_count": 0, "competitor_count": 3,
                      "top_domains": ["example.com"]},
             "competitors": [{"domain": "example.com", "tier": "Tiny (<1K)", "weakness_score": 90}]},
            {"keyword": "seo audit tool", "disruption_score": 28, "color": "🔴 RED",
             "breakdown": {"demand_signal": 80, "forum_activity": 60, "ad_gap": 0,
                           "competitor_weakness": 5, "trend_direction": 60},
             "serp": {"total_results": 5000000, "ad_count": 8, "competitor_count": 50,
                      "top_domains": ["ahrefs.com", "semrush.com"]},
             "competitors": [{"domain": "ahrefs.com", "tier": "Large (100K-1M+)", "weakness_score": 5}]},
        ]
        report = generate_report(mock, seeds=["test"])
        print(report[:500])
        print(f"\n✅ Self-test passed: report generated ({len(report)} chars)")
    else:
        main()
