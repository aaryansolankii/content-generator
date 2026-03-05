from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import Settings

logger = logging.getLogger(__name__)


class CompetitorService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def scrape_content(self, url: str) -> dict[str, Any] | None:
        try:
            async with httpx.AsyncClient(timeout=self._settings.gemini_timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Failed to fetch competitor URL: url=%s error=%s", url, exc)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = (soup.title.get_text(strip=True) if soup.title else "")[:180]

        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag["content"].strip()[:320]

        headings = [
            heading.get_text(" ", strip=True)
            for heading in soup.select("h1, h2, h3")
            if heading.get_text(" ", strip=True)
        ][:18]

        paragraph_text = [
            paragraph.get_text(" ", strip=True)
            for paragraph in soup.find_all("p")
            if paragraph.get_text(" ", strip=True)
        ]
        body_excerpt = "\n".join(paragraph_text)[:5000]

        if not any([title, meta_description, headings, body_excerpt]):
            logger.warning("Competitor page had no usable text: url=%s", url)
            return None

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "headings": headings,
            "body_excerpt": body_excerpt,
        }
