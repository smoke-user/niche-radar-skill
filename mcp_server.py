"""
Niche Radar MCP Server — wraps pipeline scripts as MCP tools.

Usage:
    # stdio mode (default, for Claude Desktop / Cursor / Cline)
    python mcp_server.py

    # SSE mode (for remote server deployment)
    python mcp_server.py --sse --port 8080
"""

import json
import os
import sys

# Add scripts/ to path so we can import them
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
sys.path.insert(0, SCRIPT_DIR)

from fastmcp import FastMCP

mcp = FastMCP(
    name="niche-radar",
    instructions=(
        "Niche discovery and validation pipeline. Use these tools to: "
        "1) check_traffic — estimate a competitor's website traffic from free signals, "
        "2) score_niche — analyze SERP + competitor traffic for a keyword → Disruption Score, "
        "3) expand_keywords — generate related keywords from a seed, "
        "4) run_pipeline — full pipeline: expand → score → rank → markdown report."
    ),
    version="1.0.0",
)


@mcp.tool
def check_traffic(domain: str) -> str:
    """Estimate competitor website traffic from free signals (indexed pages, tech stack, Wayback snapshots).

    Returns a JSON object with traffic tier (Tiny/Small/Medium/Large) and confidence score.

    Args:
        domain: Website domain to analyze (e.g. "problemsifter.com")
    """
    from check_traffic import check_traffic as _check
    result = _check(domain, verbose=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool
def score_niche(
    keyword: str,
    trend_value: int = 50,
    trend_direction: str = "stable",
    check_competitors: bool = True,
) -> str:
    """Score a niche keyword by analyzing SERP competition and competitor traffic.

    Returns Disruption Score (0-100) with Green/Yellow/Red classification.

    Args:
        keyword: Niche keyword to analyze (e.g. "AI code security scanner")
        trend_value: Google Trends interest value 0-100 (default 50)
        trend_direction: Trend direction: "rising", "stable", or "declining"
        check_competitors: Whether to check traffic of top SERP competitors
    """
    from score_niche import score_niche as _score
    result = _score(
        keyword,
        trend_value=trend_value,
        trend_direction=trend_direction,
        check_competitors=check_competitors,
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool
def expand_keywords(seed: str, depth: int = 2, max_keywords: int = 30) -> str:
    """Expand a seed keyword into 20-50 related keywords using Google Autocomplete.

    Args:
        seed: Comma-separated seed keywords (e.g. "vibe coding testing, AI QA")
        depth: Recursion depth for expansion (1-3, default 2)
        max_keywords: Maximum number of keywords to return (default 30)
    """
    from expand_keywords import expand_keywords as _expand
    seeds = [s.strip() for s in seed.split(",")]
    results = _expand(seeds, depth=depth, max_keywords=max_keywords)
    return json.dumps(results, indent=2, ensure_ascii=False)


@mcp.tool
def run_pipeline(seed: str, depth: int = 2, max_keywords: int = 15) -> str:
    """Run the full niche discovery pipeline: expand keywords → score each → rank → report.

    Returns a markdown report with Green/Yellow/Red niches sorted by Disruption Score.

    Args:
        seed: Comma-separated seed keywords (e.g. "vibe coding testing")
        depth: Keyword expansion depth (1-3, default 2)
        max_keywords: Max keywords to analyze (default 15, higher = slower)
    """
    from rank_niches import run_full_pipeline
    seeds = [s.strip() for s in seed.split(",")]
    report = run_full_pipeline(seeds, depth=depth, max_kw=max_keywords)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Niche Radar MCP Server")
    parser.add_argument("--sse", action="store_true", help="Run in SSE mode (remote server)")
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE mode")
    args = parser.parse_args()

    if args.sse:
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run()
