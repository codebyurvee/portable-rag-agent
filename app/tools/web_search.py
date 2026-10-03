"""Minimal web search tool (Tavily). Disabled cleanly if no API key is set.

Returned pages are untrusted reference data; callers must not treat their
content as instructions.
"""

import os

import httpx

TAVILY_URL = "https://api.tavily.com/search"


class WebSearchTool:
    name = "web_search"

    def __init__(self, api_key: str | None = None):
        key = api_key if api_key is not None else os.getenv("WEB_SEARCH_API_KEY")
        self.api_key = key.strip() if key else None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def run(self, query: str, max_results: int = 3) -> dict:
        if not self.enabled:
            return {"results": [], "status": "no_answer", "error": "web search not configured"}
        try:
            resp = httpx.post(
                TAVILY_URL,
                json={"api_key": self.api_key, "query": query, "max_results": max_results},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return {"results": [], "status": "error", "error": "web search request failed"}

        results = [
            {"title": r.get("title"), "url": r.get("url"), "text": r.get("content")}
            for r in data.get("results", [])
        ]
        return {"results": results, "status": "success" if results else "no_answer"}
