"""Tests for NewsAnalysisAgent."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ai.news_agent import NewsAnalysisAgent
from app.ai.models import AnalyzedNewsArticle, AgentResult


@pytest.fixture
def llm():
    return MagicMock()


@pytest.fixture
def agent(llm):
    return NewsAnalysisAgent(llm=llm, output_model=AnalyzedNewsArticle)


class TestNewsAnalysisAgent:
    def test_pdf_url_detection(self, agent):
        assert agent._is_pdf_url("https://bseindia.com/file.pdf") is True
        assert agent._is_pdf_url("https://bs.com/AnnPdfOpen.aspx?Pname=abc.pdf") is False
        assert agent._is_pdf_url("https://example.com/article.html") is False
        assert agent._is_pdf_url("https://example.com/news") is False

    @patch("app.ai.news_agent.trafilatura")
    def test_fetch_html_content(self, mock_trafilatura, agent):
        mock_trafilatura.fetch_url.return_value = "<html><body>Article content</body></html>"
        mock_trafilatura.extract.return_value = "Article content"

        result = agent._fetch_content("https://example.com/article")

        assert result == "Article content"
        mock_trafilatura.fetch_url.assert_called_once_with("https://example.com/article")

    @patch("app.ai.news_agent.pypdf")
    @patch("app.ai.news_agent.requests")
    def test_fetch_pdf_content(self, mock_requests, mock_pypdf, agent):
        mock_resp = MagicMock()
        mock_resp.content = b"%PDF-1.4 fake pdf content"
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF extracted text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pypdf.PdfReader.return_value = mock_reader

        result = agent._fetch_content("https://bseindia.com/file.pdf")

        assert result == "PDF extracted text"
        mock_requests.get.assert_called_once()

    def test_fetch_empty_url(self, agent):
        result = agent._fetch_content("")
        assert result == ""

    @patch("app.ai.news_agent.trafilatura")
    def test_fetch_network_error(self, mock_trafilatura, agent):
        mock_trafilatura.fetch_url.side_effect = ConnectionError("timeout")

        result = agent._fetch_content("https://example.com/article")
        assert result == ""

    def test_analyze_single_article(self, agent, llm):
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = AnalyzedNewsArticle(
            ticker="RELIANCE",
            news_id="12345",
            url="https://example.com/article",
            source="Test",
            pub_date="2026-09-04T12:00:00Z",
            raw_summary="Test summary",
            detailed_summary="Detailed test summary",
            impact="high",
            impact_reasoning="Test reasoning",
            trader_sentiment="bullish",
        )
        llm.with_structured_output.return_value = mock_structured_llm

        article = {"url": "https://example.com/article", "source": "Test", "summary": "Test summary"}
        result = agent._analyze_single(article, "RELIANCE", "System prompt")

        assert isinstance(result, dict)
        assert result["ticker"] == "RELIANCE"
        assert result["impact"] == "high"

    def test_run_processes_all_articles(self, agent, llm):
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = AnalyzedNewsArticle(
            ticker="RELIANCE",
            news_id="12345",
            url="https://example.com/article",
            source="Test",
            pub_date="2026-09-04T12:00:00Z",
            raw_summary="Test",
            detailed_summary="Detailed test",
            impact="medium",
            impact_reasoning="Reasoning",
            trader_sentiment="neutral",
        )
        llm.with_structured_output.return_value = mock_structured_llm

        call_count = 0

        def side_effect(article, ticker, prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("LLM failed")
            return {"url": article["url"], "source": article["source"], "summary": article["summary"]}

        agent._analyze_single = MagicMock(side_effect=side_effect)

        input_data = {
            "ticker": "RELIANCE",
            "articles": [
                {"url": "https://example.com/a1", "source": "Test", "summary": "S1"},
                {"url": "https://example.com/a2", "source": "Test", "summary": "S2"},
                {"url": "https://example.com/a3", "source": "Test", "summary": "S3"},
            ],
            "system_prompt": "System prompt",
        }
        result = agent.run(input_data)

        assert result.success is True
        assert len(result.data["articles"]) == 2
