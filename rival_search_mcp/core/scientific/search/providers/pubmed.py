"""
PubMed academic search provider via NCBI E-utilities.

No API key required (NCBI allows 3 req/sec unauthenticated, 10 req/sec
with key). Two-step protocol:
  1. esearch.fcgi returns a list of PMIDs matching the query.
  2. efetch.fcgi returns full article XML for those PMIDs.

NCBI asks that callers identify themselves via UA + tool/email params
("Each request should include an email and a tool name so we can
contact you if there is a problem"). We set both.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import httpx

from rival_search_mcp.logging.logger import logger

_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedProvider:
    """Search PubMed via NCBI E-utilities."""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "rivalsearchmcp/1.0 " "(+https://github.com/damionrashford/RivalSearchMCP)"
            ),
        }
        # NCBI recommends `tool` + `email` on every request.
        self.base_params = {
            "tool": "rivalsearchmcp",
            "email": "research@rivalsearchmcp.com",
        }

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            headers=self.headers, timeout=30.0, follow_redirects=True
        ) as client:
            try:
                search_r = await client.get(
                    f"{_EUTILS}/esearch.fcgi",
                    params={
                        **self.base_params,
                        "db": "pubmed",
                        "term": query,
                        "retmax": min(limit, 100),
                        "retmode": "json",
                        "sort": "relevance",
                    },
                )
                if search_r.status_code != 200:
                    logger.warning(
                        "pubmed esearch returned %s for %r",
                        search_r.status_code,
                        query,
                    )
                    return []
                ids = search_r.json().get("esearchresult", {}).get("idlist", [])
                if not ids:
                    logger.info("pubmed: 0 for %r", query)
                    return []

                fetch_r = await client.get(
                    f"{_EUTILS}/efetch.fcgi",
                    params={
                        **self.base_params,
                        "db": "pubmed",
                        "id": ",".join(ids[: min(limit, 20)]),
                        "retmode": "xml",
                    },
                )
                if fetch_r.status_code != 200:
                    logger.warning(
                        "pubmed efetch returned %s (body: %s)",
                        fetch_r.status_code,
                        fetch_r.text[:200],
                    )
                    return []
                papers = self._parse(fetch_r.text)
                logger.info("pubmed: %d for %r", len(papers), query)
                return papers

            except httpx.HTTPError as e:
                logger.warning("pubmed network error: %s", e)
                return []
            except Exception:
                logger.exception("pubmed unexpected error")
                return []

    def _parse(self, xml_content: str) -> List[Dict[str, Any]]:
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.warning("pubmed XML parse failed: %s", e)
            return []

        papers: List[Dict[str, Any]] = []
        for article in root.findall(".//PubmedArticle"):
            try:
                title_el = article.find(".//ArticleTitle")
                title = (title_el.text or "").strip() if title_el is not None else ""
                if not title:
                    continue

                abstract_parts = [
                    (el.text or "").strip() for el in article.findall(".//AbstractText") if el.text
                ]
                abstract = " ".join(abstract_parts)

                authors: List[Dict[str, str]] = []
                for a in article.findall(".//Author"):
                    last = a.findtext("LastName") or ""
                    fore = a.findtext("ForeName") or ""
                    name = f"{fore} {last}".strip()
                    if name:
                        authors.append({"name": name})

                pmid = (article.findtext(".//PMID") or "").strip()
                year_text = article.findtext(".//PubDate/Year")
                year = int(year_text) if year_text and year_text.isdigit() else None
                venue = article.findtext(".//Journal/Title") or ""

                papers.append(
                    {
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                        "year": year,
                        "venue": venue.strip(),
                        "paperId": pmid,
                        "source": "pubmed",
                    }
                )
            except Exception as e:
                logger.debug("pubmed article parse failed: %s", e)
        return papers

    async def get_paper_details(self, pmid: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(
            headers=self.headers, timeout=30.0, follow_redirects=True
        ) as client:
            try:
                r = await client.get(
                    f"{_EUTILS}/efetch.fcgi",
                    params={
                        **self.base_params,
                        "db": "pubmed",
                        "id": pmid,
                        "retmode": "xml",
                    },
                )
                if r.status_code != 200:
                    return None
                papers = self._parse(r.text)
                return papers[0] if papers else None
            except Exception:
                logger.exception("pubmed get_paper_details failed")
                return None

    def close(self):
        """Nothing to close; AsyncClient is used per-call."""
