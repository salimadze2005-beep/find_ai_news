from datetime import timedelta
import httpx
from app.models import NewsSource
from app.search.base import SearchProvider
from app.search.pages import valid_url, domain
from app.llm.base import ProviderError


class TavilyProvider(SearchProvider):
    def __init__(self, settings, client=None):
        self.settings = settings
        self.client = client or httpx.Client(timeout=45, trust_env=False)
        self.calls = 0

    def search(self, query, start_date, end_date, limit):
        if self.calls >= self.settings.max_search_calls:
            raise ProviderError("Search call budget exhausted")
        self.calls += 1
        data = {"query": query[:500], "max_results": min(limit, 20), "topic": "general",
                "search_depth": "basic", "include_raw_content": False,
                "end_date": (end_date + timedelta(days=1)).date().isoformat()}
        if start_date:
            data["start_date"] = start_date.date().isoformat()
        try:
            response = self.client.post("https://api.tavily.com/search", json=data,
                headers={"Authorization": "Bearer " + self.settings.tavily_api_key.get_secret_value()})
            if response.status_code != 200:
                raise ProviderError(f"Search HTTP {response.status_code}")
            return [NewsSource(title=str(r.get("title", ""))[:300], url=r["url"],
                snippet=str(r.get("content", ""))[:1200], source=domain(r["url"]))
                for r in response.json().get("results", []) if valid_url(r.get("url", ""))][:limit]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise ProviderError("Search request or response validation failed") from None
