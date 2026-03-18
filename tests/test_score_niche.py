"""Unit tests for score_niche.py — all HTTP calls are mocked."""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import score_niche as sn


EMPTY_SERP = {
    "keyword": "test",
    "total_results": 0,
    "ad_count": 0,
    "organic_domains": [],
    "has_featured_snippet": False,
    "has_people_also_ask": False,
}


class TestFetchTrends(unittest.TestCase):
    def test_returns_average_and_direction(self):
        import pandas as pd
        mock_pytrends = MagicMock()
        mock_pt = MagicMock()
        # Simulate rising trend: low first half, high second half
        values = [10, 15, 12, 50, 60, 55, 70, 65, 80, 75, 85, 90]
        df = pd.DataFrame({"my keyword": values})
        mock_pt.interest_over_time.return_value = df
        mock_pytrends.request.TrendReq.return_value = mock_pt
        with patch.dict("sys.modules", {"pytrends": mock_pytrends,
                                        "pytrends.request": mock_pytrends.request}):
            value, direction = sn.fetch_trends("my keyword")
        assert isinstance(value, int)
        assert direction == "rising"

    def test_declining_trend(self):
        import pandas as pd
        mock_pytrends = MagicMock()
        mock_pt = MagicMock()
        values = [90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 5, 3]
        df = pd.DataFrame({"brand": values})
        mock_pt.interest_over_time.return_value = df
        mock_pytrends.request.TrendReq.return_value = mock_pt
        with patch.dict("sys.modules", {"pytrends": mock_pytrends,
                                        "pytrends.request": mock_pytrends.request}):
            value, direction = sn.fetch_trends("brand")
        assert direction == "declining"

    def test_exception_returns_default(self):
        mock_pytrends = MagicMock()
        mock_pytrends.request.TrendReq.side_effect = Exception("rate limited")
        with patch.dict("sys.modules", {"pytrends": mock_pytrends,
                                        "pytrends.request": mock_pytrends.request}):
            value, direction = sn.fetch_trends("any")
        assert value == 50
        assert direction == "unknown"

    def test_empty_dataframe_returns_default(self):
        import pandas as pd
        mock_pytrends = MagicMock()
        mock_pt = MagicMock()
        mock_pt.interest_over_time.return_value = pd.DataFrame()
        mock_pytrends.request.TrendReq.return_value = mock_pt
        with patch.dict("sys.modules", {"pytrends": mock_pytrends,
                                        "pytrends.request": mock_pytrends.request}):
            value, direction = sn.fetch_trends("any")
        assert value == 50
        assert direction == "unknown"


class TestScoreNiche(unittest.TestCase):
    @patch("score_niche.analyze_serp", return_value=EMPTY_SERP)
    def test_no_competitors_gives_high_weakness(self, _):
        result = sn.score_niche("test niche", trend_value=60, trend_direction="rising",
                                check_competitors=False)
        assert result["breakdown"]["competitor_weakness"] == 80.0

    @patch("score_niche.analyze_serp", return_value={**EMPTY_SERP, "ad_count": 8})
    def test_many_ads_lower_ad_gap(self, _):
        result = sn.score_niche("saturated", trend_value=50, trend_direction="stable",
                                check_competitors=False)
        assert result["breakdown"]["ad_gap"] == 0.0

    @patch("score_niche.analyze_serp", return_value=EMPTY_SERP)
    def test_green_score_with_good_signals(self, _):
        result = sn.score_niche("golden niche", trend_value=90, trend_direction="rising",
                                forum_mentions=100, check_competitors=False)
        assert result["disruption_score"] >= 70
        assert "GREEN" in result["color"]

    @patch("score_niche.analyze_serp", return_value={**EMPTY_SERP, "ad_count": 8})
    def test_red_score_with_bad_signals(self, _):
        result = sn.score_niche("dead market", trend_value=5, trend_direction="declining",
                                forum_mentions=1, check_competitors=False)
        assert result["disruption_score"] < 40
        assert "RED" in result["color"]

    @patch("score_niche.check_traffic", return_value={"traffic_tier": "Tiny (<1K)"})
    @patch("score_niche.analyze_serp", return_value={
        **EMPTY_SERP, "organic_domains": ["tiny1.com", "tiny2.com", "tiny3.com"]
    })
    def test_competitor_weakness_from_tier(self, _, mock_ct):
        result = sn.score_niche("niche kw", trend_value=50, trend_direction="stable",
                                check_competitors=True)
        assert result["breakdown"]["competitor_weakness"] == 90.0
        assert len(result["competitors"]) == 3

    @patch("score_niche.fetch_trends", return_value=(75, "rising"))
    @patch("score_niche.analyze_serp", return_value=EMPTY_SERP)
    def test_auto_fetch_trends_when_defaults(self, _, mock_ft):
        result = sn.score_niche("auto trend kw", check_competitors=False)
        mock_ft.assert_called_once_with("auto trend kw")
        assert result["breakdown"]["demand_signal"] == 75.0
        assert result["breakdown"]["trends_source"] == "auto"

    @patch("score_niche.fetch_trends")
    @patch("score_niche.analyze_serp", return_value=EMPTY_SERP)
    def test_no_auto_fetch_when_explicit(self, _, mock_ft):
        sn.score_niche("explicit kw", trend_value=40, trend_direction="declining",
                       check_competitors=False)
        mock_ft.assert_not_called()

    @patch("score_niche.fetch_trends", return_value=(50, "unknown"))
    @patch("score_niche.analyze_serp", return_value=EMPTY_SERP)
    def test_trends_source_default_when_fetch_fails(self, _, mock_ft):
        result = sn.score_niche("fallback kw", check_competitors=False)
        assert result["breakdown"]["trends_source"] == "default"

    @patch("score_niche.analyze_serp", return_value=EMPTY_SERP)
    def test_result_structure(self, _):
        result = sn.score_niche("struct kw", trend_value=50, trend_direction="stable",
                                check_competitors=False)
        assert "keyword" in result
        assert "disruption_score" in result
        assert "color" in result
        assert "breakdown" in result
        assert "serp" in result
        assert "competitors" in result
        bd = result["breakdown"]
        assert "demand_signal" in bd
        assert "forum_activity" in bd
        assert "ad_gap" in bd
        assert "competitor_weakness" in bd
        assert "trend_direction" in bd
        assert "trends_source" in bd


if __name__ == "__main__":
    unittest.main()
