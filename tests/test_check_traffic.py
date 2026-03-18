"""Unit tests for check_traffic.py — all HTTP calls are mocked."""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import check_traffic as ct


class TestCleanDomain(unittest.TestCase):
    def test_strips_https(self):
        assert ct.clean_domain("https://www.example.com/path") == "example.com"

    def test_strips_www(self):
        assert ct.clean_domain("www.example.com") == "example.com"

    def test_normalizes_case(self):
        assert ct.clean_domain("EXAMPLE.COM") == "example.com"

    def test_plain_domain(self):
        assert ct.clean_domain("example.com") == "example.com"


class TestBrandFromDomain(unittest.TestCase):
    def test_extracts_brand(self):
        assert ct._brand_from_domain("problemsifter.com") == "problemsifter"

    def test_subdomain_is_preserved(self):
        assert ct._brand_from_domain("app.example.com") == "app"


class TestCheckIndexedPages(unittest.TestCase):
    def _make_response(self, text: str, status: int = 200) -> MagicMock:
        r = MagicMock()
        r.status_code = status
        r.text = text
        return r

    @patch("check_traffic.fetch")
    def test_primary_regex(self, mock_fetch):
        mock_fetch.return_value = self._make_response(
            '<div id="result-stats">About 12,345 results</div>'
        )
        assert ct.check_indexed_pages("example.com") == 12345

    @patch("check_traffic.fetch")
    def test_no_results(self, mock_fetch):
        mock_fetch.return_value = self._make_response(
            "Your search - site:example.com - did not match any documents."
        )
        assert ct.check_indexed_pages("example.com") == 0

    @patch("check_traffic.fetch")
    def test_fallback_h3_count(self, mock_fetch):
        mock_fetch.return_value = self._make_response(
            "<h3>Result one</h3><h3>Result two</h3>"
        )
        assert ct.check_indexed_pages("example.com") == 10

    @patch("check_traffic.fetch")
    def test_http_error(self, mock_fetch):
        mock_fetch.return_value = self._make_response("", status=429)
        assert ct.check_indexed_pages("example.com") == 0

    @patch("check_traffic.fetch")
    def test_fetch_none(self, mock_fetch):
        mock_fetch.return_value = None
        assert ct.check_indexed_pages("example.com") == 0


class TestCheckDomainAge(unittest.TestCase):
    def test_returns_positive_age(self):
        from datetime import datetime as real_dt
        mock_whois = MagicMock()
        mock_whois.whois.return_value.creation_date = real_dt(2020, 1, 1)
        with patch.dict("sys.modules", {"whois": mock_whois}):
            age = ct.check_domain_age("example.com")
        # Domain created in 2020, current date is ~2026 → age should be > 5
        assert age > 5.0

    def test_list_creation_date_is_handled(self):
        from datetime import datetime as real_dt
        mock_whois = MagicMock()
        mock_whois.whois.return_value.creation_date = [real_dt(2020, 6, 1), real_dt(2020, 6, 2)]
        with patch.dict("sys.modules", {"whois": mock_whois}):
            age = ct.check_domain_age("example.com")
        assert age > 0.0

    def test_import_error_returns_zero(self):
        with patch.dict("sys.modules", {"whois": None}):
            age = ct.check_domain_age("example.com")
        assert age == 0.0

    def test_exception_returns_zero(self):
        mock_whois = MagicMock()
        mock_whois.whois.side_effect = Exception("WHOIS failed")
        with patch.dict("sys.modules", {"whois": mock_whois}):
            age = ct.check_domain_age("example.com")
        assert age == 0.0


class TestCheckBrandTrend(unittest.TestCase):
    def test_returns_average(self):
        import pandas as pd
        mock_pytrends = MagicMock()
        mock_pt_instance = MagicMock()
        df = pd.DataFrame({"mybrand": [20, 40, 60, 80]})
        mock_pt_instance.interest_over_time.return_value = df
        mock_pytrends.request.TrendReq.return_value = mock_pt_instance
        with patch.dict("sys.modules", {"pytrends": mock_pytrends,
                                        "pytrends.request": mock_pytrends.request}):
            result = ct.check_brand_trend("mybrand.com")
        assert result == 50

    def test_exception_returns_zero(self):
        mock_pytrends = MagicMock()
        mock_pytrends.request.TrendReq.side_effect = Exception("rate limited")
        with patch.dict("sys.modules", {"pytrends": mock_pytrends,
                                        "pytrends.request": mock_pytrends.request}):
            result = ct.check_brand_trend("example.com")
        assert result == 0


class TestEstimateTier(unittest.TestCase):
    def _signals(self, **kwargs) -> ct.TrafficSignals:
        s = ct.TrafficSignals(domain="test.com")
        for k, v in kwargs.items():
            setattr(s, k, v)
        return s

    def test_large_site(self):
        s = self._signals(indexed_pages=50000, domain_age_years=7, brand_trend=80,
                          wayback_snapshots=10000, has_analytics=True, has_custom_build=True,
                          tech_stack="Next.js", has_og_tags=True, has_twitter_card=True)
        tier, score = ct.estimate_tier(s)
        assert tier == "Large (100K-1M+)"
        assert score >= 70

    def test_tiny_site(self):
        s = self._signals()
        tier, score = ct.estimate_tier(s)
        assert tier == "Tiny (<1K)"
        assert score < 25

    def test_medium_site(self):
        s = self._signals(indexed_pages=5000, domain_age_years=3, has_analytics=True)
        tier, score = ct.estimate_tier(s)
        assert tier in ("Medium (10K-100K)", "Small (1K-10K)")

    def test_domain_age_contributes(self):
        s_old = self._signals(domain_age_years=6)
        s_new = self._signals(domain_age_years=0)
        _, score_old = ct.estimate_tier(s_old)
        _, score_new = ct.estimate_tier(s_new)
        assert score_old > score_new

    def test_brand_trend_contributes(self):
        s_high = self._signals(brand_trend=80)
        s_low = self._signals(brand_trend=0)
        _, score_high = ct.estimate_tier(s_high)
        _, score_low = ct.estimate_tier(s_low)
        assert score_high > score_low


class TestCheckTrafficCache(unittest.TestCase):
    def setUp(self):
        ct._traffic_cache.clear()

    @patch("check_traffic.check_indexed_pages", return_value=100)
    @patch("check_traffic.check_domain_age", return_value=3.0)
    @patch("check_traffic.check_brand_trend", return_value=0)
    @patch("check_traffic.check_homepage", return_value={
        "has_og_tags": False, "has_twitter_card": False, "has_analytics": False,
        "has_custom_build": False, "tech_stack": "Custom", "meta_description": "",
        "title": "", "status_code": 200,
    })
    @patch("check_traffic.check_wayback", return_value=100)
    def test_result_is_cached(self, mock_wb, mock_hp, mock_bt, mock_da, mock_ip):
        result1 = ct.check_traffic("cached.com", verbose=False)
        result2 = ct.check_traffic("cached.com", verbose=False)
        assert result1 is result2
        # check_indexed_pages should only be called once
        mock_ip.assert_called_once()

    @patch("check_traffic.check_indexed_pages", return_value=0)
    @patch("check_traffic.check_domain_age", return_value=0.0)
    @patch("check_traffic.check_brand_trend", return_value=0)
    @patch("check_traffic.check_homepage", return_value={
        "has_og_tags": False, "has_twitter_card": False, "has_analytics": False,
        "has_custom_build": False, "tech_stack": "unknown", "meta_description": "",
        "title": "", "status_code": 0,
    })
    @patch("check_traffic.check_wayback", return_value=0)
    def test_result_structure(self, *_):
        result = ct.check_traffic("struct.com", verbose=False)
        assert "domain" in result
        assert "traffic_tier" in result
        assert "confidence_score" in result
        assert "signals" in result
        assert "checked_at" in result
        assert result["signals"]["domain_age_years"] == 0.0
        assert result["signals"]["brand_trend"] == 0


if __name__ == "__main__":
    unittest.main()
