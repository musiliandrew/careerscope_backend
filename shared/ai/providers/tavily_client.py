import os
import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TavilyClient:
    """
    A lightweight HTTP wrapper for the Tavily Search API.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> str:
        """
        Executes a search and returns a concatenated string of the result snippets.
        """
        if not self.api_key:
            logger.warning("TAVILY_API_KEY is missing. Returning empty search results.")
            return ""

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": max_results,
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            snippets = [f"Source: {res.get('url')}\nContent: {res.get('content')}" for res in results]
            
            return "\n\n---\n\n".join(snippets)
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return ""
