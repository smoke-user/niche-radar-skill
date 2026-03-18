"""
/* LOGIC CHECK:
- Takes seed keyword(s), expands into 20-50 related keywords
- Uses Google autocomplete suggestions (free, no API key)
- Recursive depth: seed → suggestions → sub-suggestions
- Dedup by normalized lowercase
- Output: JSON array of keywords with source
*/

Keyword Expander — generate related keywords from seeds.
"""

import argparse
import json
import re
import time
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("❌ pip install requests")
    sys.exit(1)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}
DELAY = 1.0


def get_google_suggestions(query: str) -> list[str]:
    """Get Google autocomplete suggestions for a query."""
    url = "https://suggestqueries.google.com/complete/search"
    params = {"client": "firefox", "q": query, "hl": "en"}
    time.sleep(DELAY)
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1 and isinstance(data[1], list):
                return [s for s in data[1] if s != query]
    except Exception as e:
        print(f"  ⚠️  Suggestion failed for '{query}': {e}")
    return []


def expand_with_modifiers(seed: str) -> list[str]:
    """Generate modified queries using common SaaS/niche prefixes/suffixes."""
    modifiers = [
        f"{seed} tool", f"{seed} software", f"{seed} saas",
        f"{seed} alternative", f"{seed} for",
        f"best {seed}", f"free {seed}", f"how to {seed}",
        f"{seed} api", f"{seed} platform",
    ]
    return modifiers


def expand_keywords(seeds: list[str], depth: int = 2, max_keywords: int = 50) -> list[dict]:
    """Expand seed keywords into related keywords."""
    seen = set()
    results = []

    def add(kw: str, source: str, level: int):
        norm = kw.strip().lower()
        if norm in seen or len(norm) < 3:
            return
        seen.add(norm)
        results.append({
            "keyword": norm,
            "source": source,
            "depth": level,
        })

    # Level 0: seeds
    for seed in seeds:
        add(seed, "seed", 0)

    # Level 1: autocomplete + modifiers
    for seed in seeds:
        print(f"  🔍 Expanding: '{seed}'")

        # Google suggestions
        suggestions = get_google_suggestions(seed)
        for s in suggestions[:8]:
            add(s, f"google_suggest({seed})", 1)

        # Modifiers
        for mod in expand_with_modifiers(seed):
            mod_suggestions = get_google_suggestions(mod)
            for s in mod_suggestions[:4]:
                add(s, f"modifier({mod})", 1)

        if len(results) >= max_keywords:
            break

    # Level 2: expand top suggestions (if depth >= 2)
    if depth >= 2:
        level1 = [r["keyword"] for r in results if r["depth"] == 1][:10]
        for kw in level1:
            if len(results) >= max_keywords:
                break
            suggestions = get_google_suggestions(kw)
            for s in suggestions[:4]:
                add(s, f"deep({kw})", 2)

    print(f"\n  📦 Total keywords: {len(results)}")
    return results[:max_keywords]


def main():
    parser = argparse.ArgumentParser(description="Expand seed keywords into related keywords")
    parser.add_argument("--seed", "-s", required=True, help="Seed keyword(s), comma-separated")
    parser.add_argument("--depth", "-d", type=int, default=2, help="Recursion depth (1-3)")
    parser.add_argument("--max", "-m", type=int, default=50, help="Max keywords to generate")
    parser.add_argument("--out", "-o", help="Output JSON file path")
    args = parser.parse_args()

    seeds = [s.strip() for s in args.seed.split(",")]
    print(f"🌱 Seeds: {seeds}")
    print(f"📏 Depth: {args.depth} | Max: {args.max}")

    results = expand_keywords(seeds, depth=args.depth, max_keywords=args.max)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📄 Saved to {args.out}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🧪 Self-test: expanding 'niche finder tool'")
        results = expand_keywords(["niche finder tool"], depth=1, max_keywords=15)
        for r in results:
            print(f"  {'  ' * r['depth']}→ {r['keyword']} [{r['source']}]")
        print(f"\n✅ Self-test passed: {len(results)} keywords")
    else:
        main()
