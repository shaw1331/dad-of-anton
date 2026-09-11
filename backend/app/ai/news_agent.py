from __future__ import annotations

import logging
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

import pypdf
import requests
import trafilatura
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.ai.audit import build_audit, invocation_started
from app.ai.factory import AgentFactory
from app.ai.interfaces import AgentGraph
from app.ai.models import AgentResult, AnalyzedNewsArticle

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.bseindia.com/",
}


class NewsAnalysisAgent(AgentGraph):
    """LangGraph agent for news analysis using an injected LLM.

    Fetches full article content via trafilatura (HTML) or pypdf (PDFs),
    then uses the LLM to summarize, grade impact, and determine trader sentiment.
    Processes articles one at a time to stay within LLM context limits.
    """

    name = "news_analysis"

    def __init__(self, llm: BaseChatModel, output_model: type[BaseModel]) -> None:
        self.llm = llm
        self.output_model = output_model

    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL points to a PDF file."""
        parsed = urlparse(url)
        return (
            parsed.path.lower().endswith(".pdf")
            or ".pdf" in parsed.query.lower()
        )

    def _fetch_pdf(self, url: str) -> str:
        """Fetch and extract text from a PDF URL."""
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=30)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "").lower()
            if "pdf" not in content_type and not resp.content.startswith(b"%PDF"):
                logger.warning(
                    "URL did not return a PDF: %s (Content-Type: %s)",
                    url,
                    content_type,
                )
                return ""

            reader = pypdf.PdfReader(BytesIO(resp.content))

            pages = []
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"\n--- PAGE {page_number} ---\n{text.strip()}")

            return "\n".join(pages)

        except requests.RequestException:
            logger.warning("Failed to fetch PDF from %s", url)
            return ""
        except Exception:
            logger.exception("Failed to extract PDF from %s", url)
            return ""

    def _fetch_html(self, url: str) -> str:
        """Fetch and extract text from an HTML URL using trafilatura."""
        try:
            downloaded = trafilatura.fetch_url(url)
            return trafilatura.extract(downloaded) or ""
        except Exception:
            logger.warning("Failed to fetch content for %s", url)
            return ""

    def _fetch_content(self, url: str) -> str:
        """Fetch full article content from a URL (HTML or PDF)."""
        if not url:
            return ""
        if self._is_pdf_url(url):
            return self._fetch_pdf(url)
        return self._fetch_html(url)

    def _build_analysis_prompt(self, article: dict, ticker: str) -> str:
        """Fetch article content and format the untrusted-data prompt."""
        full_content = self._fetch_content(article.get("url", ""))
        summary = article.get("summary", "")
        content_text = full_content if full_content else "[Could not extract content]"
        return (
            f"Analyze this news article for {ticker}:\n\n"
            f"Source: {article.get('source', 'Unknown')}\n"
            f"Date: {article.get('pub_date', 'Unknown')}\n"
            f"URL: {article.get('url', 'N/A')}\n"
            f"Summary: {summary}\n"
            f"Full Content: {content_text}"
        )

    def _analyze_single(self, analysis_prompt: str, system_prompt: str) -> dict:
        """Analyze one prepared article prompt with the LLM."""
        structured_llm = self.llm.with_structured_output(AnalyzedNewsArticle)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis_prompt),
        ]
        result = structured_llm.invoke(messages)
        return result.model_dump()

    def run(self, input_data: dict[str, Any]) -> AgentResult:
        ticker = input_data["ticker"]
        articles = input_data["articles"]
        system_prompt = input_data["system_prompt"]

        analyzed = []
        audits = []
        for article in articles:
            analysis_prompt = self._build_analysis_prompt(article, ticker)
            started_at = invocation_started()
            try:
                result = self._analyze_single(analysis_prompt, system_prompt)
                analyzed.append(result)
                audits.append(build_audit(
                    agent_name=self.name,
                    context=getattr(self, "audit_context", None),
                    prompt_version=input_data.get("prompt_version", "unversioned"),
                    schema_version=AnalyzedNewsArticle.__name__,
                    system_prompt=system_prompt,
                    analysis_prompt=analysis_prompt,
                    started_at=started_at,
                    output=result,
                ))
            except Exception as error:
                logger.warning("Failed to analyze article %s for %s",
                               article.get("url", ""), ticker)
                audits.append(build_audit(
                    agent_name=self.name,
                    context=getattr(self, "audit_context", None),
                    prompt_version=input_data.get("prompt_version", "unversioned"),
                    schema_version=AnalyzedNewsArticle.__name__,
                    system_prompt=system_prompt,
                    analysis_prompt=analysis_prompt,
                    started_at=started_at,
                    error=str(error),
                ))

        return AgentResult(
            success=True,
            data={"articles": analyzed, "ticker": ticker,
                  "total_articles": len(analyzed)},
            error=None,
            graph_name=self.name,
            audits=audits,
        )


AgentFactory.register("news_analysis", NewsAnalysisAgent)
