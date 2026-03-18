"""
Competitor Traffic Estimator — estimate site traffic from free signals.

Signals used:
  1. Indexed pages   — Google site: query
  2. Domain age      — WHOIS lookup (python-whois)
  3. Brand trend     — Google Trends (pytrends, best-effort)
  4. Tech stack/meta — HTML homepage analysis
  5. Wayback count   — Wayback CDX API

Rate limiting: 2s delay between HTTP calls.
Results are cached in-memory within a process (useful for pipeline runs).
"""

import argparse
import json
import re
import time
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ pip install requests beautifulsoup4 lxml")
    sys.exit(1)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
DELAY = 2.0  # seconds between requests

# In-memory cache for the lifetime of the process (avoids re-checking same domain in a pipeline)
_traffic_cache: dict[str, dict] = {}


@dataclass
class TrafficSignals:
    domain: str
    indexed_pages: int = 0
    domain_age_years: float = 0.0
    brand_trend: int = 0
    has_og_tags: bool = False
    has_twitter_card: bool = False
    has_analytics: bool = False
    has_custom_build: bool = False
    tech_stack: str = "unknown"
    wayback_snapshots: int = 0
    meta_description: str = ""
    title: str = ""
    status_code: int = 0
    error: str = ""


def clean_domain(raw: str) -> str:
    """Normalize domain input."""
    raw = raw.strip().lower()
    if raw.startswith("http"):
        return urlparse(raw).netloc.replace("www.", "")
    return raw.replace("www.", "").split("/")[0]


def _brand_from_domain(domain: str) -> str:
    """Extract brand name from domain (e.g. 'problemsifter.com' → 'problemsifter')."""
    return domain.split(".")[0]


def fetch(url: str, timeout: int = 10) -> Optional[requests.Response]:
    """Safe HTTP GET with rate-limit delay."""
    time.sleep(DELAY)
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r
    except Exception as e:
        print(f"  ⚠️  Fetch failed: {url} — {e}")
        return None


def check_indexed_pages(domain: str) -> int:
    """Estimate indexed pages via Google 'site:' query."""
    url = f"https://www.google.com/search?q=site:{domain}&num=1"
    r = fetch(url)
    if not r or r.status_code != 200:
        return 0

    # Primary: "About X results" text
    match = re.search(r"About ([\d,]+) results", r.text)
    if match:
        return int(match.group(1).replace(",", ""))

    # Secondary: localized result stats div (non-English Google)
    stats_div = BeautifulSoup(r.text, "lxml").find("div", id="result-stats")
    if stats_div:
        nums = re.findall(r"[\d,]+", stats_div.get_text())
        if nums:
            try:
                return int(nums[0].replace(",", ""))
            except ValueError:
                pass

    # Tertiary: count organic result headings as a proxy
    soup = BeautifulSoup(r.text, "lxml")
    if "did not match any documents" in r.text:
        return 0
    h3_count = len(soup.find_all("h3"))
    if h3_count > 0:
        # We got results but can't read the exact count — treat as small indexed site
        return 10
    return 0


def check_domain_age(domain: str) -> float:
    """Return domain age in years using WHOIS. Returns 0.0 on failure."""
    try:
        import whois  # python-whois package
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date and isinstance(creation_date, datetime):
            age = (datetime.now() - creation_date).days / 365.25
            return round(max(0.0, age), 1)
    except Exception:
        pass
    return 0.0


def check_brand_trend(domain: str) -> int:
    """Return Google Trends interest (0-100) for the brand name. Returns 0 on failure."""
    brand = _brand_from_domain(domain)
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-US", tz=360, timeout=(5, 20), retries=1, backoff_factor=0.5)
        pt.build_payload([brand], timeframe="today 12-m")
        df = pt.interest_over_time()
        if df is not None and not df.empty and brand in df.columns:
            return int(df[brand].mean())
    except Exception:
        pass
    return 0


def check_homepage(domain: str) -> dict:
    """Analyze homepage HTML for signals."""
    signals = {
        "has_og_tags": False,
        "has_twitter_card": False,
        "has_analytics": False,
        "has_custom_build": False,
        "tech_stack": "unknown",
        "meta_description": "",
        "title": "",
        "status_code": 0,
    }
    url = f"https://{domain}"
    r = fetch(url)
    if not r:
        r = fetch(f"http://{domain}")
    if not r:
        return signals

    signals["status_code"] = r.status_code
    if r.status_code != 200:
        return signals

    soup = BeautifulSoup(r.text, "lxml")

    if soup.title:
        signals["title"] = soup.title.string or ""

    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        signals["meta_description"] = meta.get("content", "")

    if soup.find("meta", attrs={"property": re.compile(r"^og:")}):
        signals["has_og_tags"] = True

    if soup.find("meta", attrs={"name": re.compile(r"^twitter:")}):
        signals["has_twitter_card"] = True

    html_lower = r.text.lower()
    analytics_markers = [
        "google-analytics.com", "googletagmanager.com", "gtag(",
        "hotjar.com", "amplitude.com", "mixpanel.com",
        "plausible.io", "segment.com", "posthog.com",
    ]
    if any(m in html_lower for m in analytics_markers):
        signals["has_analytics"] = True

    if "wp-content" in html_lower or "wordpress" in html_lower:
        signals["tech_stack"] = "WordPress"
    elif "next" in html_lower and "__next" in html_lower:
        signals["tech_stack"] = "Next.js"
        signals["has_custom_build"] = True
    elif "nuxt" in html_lower:
        signals["tech_stack"] = "Nuxt.js"
        signals["has_custom_build"] = True
    elif "_app" in html_lower or "react" in html_lower:
        signals["tech_stack"] = "React SPA"
        signals["has_custom_build"] = True
    elif "wix.com" in html_lower:
        signals["tech_stack"] = "Wix"
    elif "squarespace" in html_lower:
        signals["tech_stack"] = "Squarespace"
    elif "webflow" in html_lower:
        signals["tech_stack"] = "Webflow"
    else:
        signals["has_custom_build"] = True
        signals["tech_stack"] = "Custom"

    return signals


def check_wayback(domain: str) -> int:
    """Count Wayback Machine snapshots (proxy for historical traffic)."""
    url = f"https://web.archive.org/cdx/search/cdx?url={domain}&output=json&limit=1&fl=statuscode"
    r = fetch(url, timeout=15)
    if not r or r.status_code != 200:
        return 0
    count_url = (
        f"https://web.archive.org/cdx/search/cdx?url={domain}/*"
        f"&output=json&limit=0&showNumPages=true"
    )
    r2 = fetch(count_url, timeout=15)
    if not r2 or r2.status_code != 200:
        return 0
    try:
        pages = int(r2.text.strip())
        return pages * 10  # Each CDX page ≈ 10 snapshots
    except (ValueError, TypeError):
        return 0


def estimate_tier(signals: TrafficSignals) -> tuple[str, int]:
    """Classify traffic tier and return a confidence score (0–130 scale).

    Scoring per references/traffic_signals.md:
      indexed_pages  → up to 30 pts
      domain_age     → up to 20 pts
      brand_trend    → up to 30 pts
      social/meta    → up to 15 pts
      wayback        → up to 15 pts
      tech/analytics → up to 20 pts
    Thresholds: Large ≥70 | Medium ≥45 | Small ≥25 | Tiny <25
    """
    score = 0

    # Indexed pages (up to 30)
    if signals.indexed_pages > 10000:
        score += 30
    elif signals.indexed_pages > 1000:
        score += 20
    elif signals.indexed_pages > 100:
        score += 10
    elif signals.indexed_pages > 10:
        score += 5

    # Domain age (up to 20)
    if signals.domain_age_years > 5:
        score += 20
    elif signals.domain_age_years > 2:
        score += 10
    elif signals.domain_age_years > 1:
        score += 5

    # Brand Google Trends (up to 30)
    if signals.brand_trend > 50:
        score += 30
    elif signals.brand_trend > 20:
        score += 15
    elif signals.brand_trend > 5:
        score += 5

    # Wayback snapshots (up to 15)
    if signals.wayback_snapshots > 5000:
        score += 15
    elif signals.wayback_snapshots > 500:
        score += 10
    elif signals.wayback_snapshots > 50:
        score += 5

    # Social / meta signals (up to 10)
    if signals.has_og_tags:
        score += 5
    if signals.has_twitter_card:
        score += 5

    # Tech investment (up to 20)
    if signals.has_analytics:
        score += 10
    if signals.has_custom_build:
        score += 5
    if signals.tech_stack in ("Next.js", "Nuxt.js", "React SPA"):
        score += 5

    # Classify (thresholds from traffic_signals.md)
    if score >= 70:
        tier = "Large (100K-1M+)"
    elif score >= 45:
        tier = "Medium (10K-100K)"
    elif score >= 25:
        tier = "Small (1K-10K)"
    else:
        tier = "Tiny (<1K)"

    return tier, score


def check_traffic(domain: str, verbose: bool = True) -> dict:
    """Full traffic estimation for a domain. Results are cached in-memory."""
    domain = clean_domain(domain)

    if domain in _traffic_cache:
        if verbose:
            print(f"\n💾 Cache hit: {domain}")
        return _traffic_cache[domain]

    if verbose:
        print(f"\n🔍 Analyzing: {domain}")
        print("=" * 50)

    signals = TrafficSignals(domain=domain)

    # 1. Indexed pages
    if verbose:
        print("  📄 Checking indexed pages...")
    signals.indexed_pages = check_indexed_pages(domain)
    if verbose:
        print(f"     → {signals.indexed_pages:,} pages")

    # 2. Domain age
    if verbose:
        print("  📅 Checking domain age (WHOIS)...")
    signals.domain_age_years = check_domain_age(domain)
    if verbose:
        print(f"     → {signals.domain_age_years:.1f} years")

    # 3. Brand trend
    if verbose:
        print(f"  📈 Checking brand trend ('{_brand_from_domain(domain)}')...")
    signals.brand_trend = check_brand_trend(domain)
    if verbose:
        print(f"     → Trends interest: {signals.brand_trend}/100")

    # 4. Homepage analysis
    if verbose:
        print("  🏠 Analyzing homepage...")
    hp = check_homepage(domain)
    signals.has_og_tags = hp["has_og_tags"]
    signals.has_twitter_card = hp["has_twitter_card"]
    signals.has_analytics = hp["has_analytics"]
    signals.has_custom_build = hp["has_custom_build"]
    signals.tech_stack = hp["tech_stack"]
    signals.meta_description = hp["meta_description"]
    signals.title = hp["title"]
    signals.status_code = hp["status_code"]
    if verbose:
        print(f"     → Tech: {signals.tech_stack} | OG: {signals.has_og_tags} | "
              f"Analytics: {signals.has_analytics}")

    # 5. Wayback snapshots
    if verbose:
        print("  📸 Checking Wayback Machine...")
    signals.wayback_snapshots = check_wayback(domain)
    if verbose:
        print(f"     → ~{signals.wayback_snapshots:,} snapshots")

    tier, confidence = estimate_tier(signals)

    result = {
        "domain": domain,
        "traffic_tier": tier,
        "confidence_score": confidence,
        "signals": asdict(signals),
        "checked_at": datetime.now().isoformat(),
    }

    _traffic_cache[domain] = result

    if verbose:
        print(f"\n  📊 Result: {tier} (confidence: {confidence}/130)")
        print("=" * 50)

    return result


def main():
    parser = argparse.ArgumentParser(description="Estimate competitor website traffic")
    parser.add_argument("--domain", "-d", required=True, help="Domain to check (e.g. problemsifter.com)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--out", "-o", help="Save result to file")
    args = parser.parse_args()

    result = check_traffic(args.domain, verbose=not args.json)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Saved to {args.out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🧪 Self-test mode: checking problemsifter.com")
        result = check_traffic("problemsifter.com")
        print(f"\n✅ Self-test passed: {result['traffic_tier']}")
    else:
        main()
