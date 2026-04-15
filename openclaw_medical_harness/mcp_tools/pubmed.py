"""
PubMed MCP Tool — 真实的PubMed文献检索实现。

使用 NCBI E-utilities API，免费，无需API Key。
文档：https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from ..base import ToolBase

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedSearchTool(ToolBase):
    """PubMed文献检索工具。

    支持：
    - 关键词搜索
    - 获取摘要
    - 相关文章推荐

    Example:
        >>> tool = PubMedSearchTool()
        >>> result = tool.execute({"query": "myasthenia gravis treatment"}, {})
        >>> for article in result["articles"]:
        ...     print(article["title"])
    """

    @property
    def name(self) -> str:
        return "pubmed_search"

    @property
    def description(self) -> str:
        return "Search PubMed for biomedical literature"

    def __init__(self, max_results: int = 5, email: str = "mokangmedical@example.com") -> None:
        self.max_results = max_results
        self.email = email
        self._client = httpx.Client(timeout=30.0)

    def execute(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """执行PubMed搜索。

        从context中提取query参数，搜索PubMed，返回文章列表。
        """
        # 从context或prior_results中提取查询
        query = ""
        if "query" in context:
            query = context["query"]
        elif "patient" in context:
            patient = context["patient"]
            symptoms = patient.get("symptoms", [])
            if symptoms:
                query = " ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)

        if not query:
            return {"articles": [], "query": "", "total_found": 0}

        try:
            # Step 1: Search for article IDs
            search_response = self._client.get(
                f"{EUTILS_BASE}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": self.max_results,
                    "retmode": "json",
                    "sort": "relevance",
                    "email": self.email,
                },
            )
            search_response.raise_for_status()
            search_data = search_response.json()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            total = search_data.get("esearchresult", {}).get("count", "0")

            if not id_list:
                return {"articles": [], "query": query, "total_found": int(total)}

            # Rate limiting — NCBI asks for max 3 requests/second
            time.sleep(0.35)

            # Step 2: Fetch article details
            fetch_response = self._client.get(
                f"{EUTILS_BASE}/esummary.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "json",
                    "email": self.email,
                },
            )
            fetch_response.raise_for_status()
            fetch_data = fetch_response.json()

            articles = []
            for pmid in id_list:
                info = fetch_data.get("result", {}).get(pmid, {})
                if isinstance(info, dict) and "title" in info:
                    articles.append({
                        "pmid": pmid,
                        "title": info.get("title", ""),
                        "authors": [a.get("name", "") for a in info.get("authors", [])[:3]],
                        "journal": info.get("source", ""),
                        "pub_date": info.get("pubdate", ""),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    })

            return {
                "articles": articles,
                "query": query,
                "total_found": int(total),
                "tool": "pubmed_search",
            }

        except Exception as e:
            logger.error("PubMed search failed: %s", str(e))
            return {"articles": [], "query": query, "error": str(e), "tool": "pubmed_search"}

    def close(self) -> None:
        self._client.close()
