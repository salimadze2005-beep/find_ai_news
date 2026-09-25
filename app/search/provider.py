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
        return self._search(query, start_date, end_date, limit, "general")

    def discover(self, query, start_date, end_date, limit):
        found = self._search(query, start_date, end_date, limit, "news")
        if len(found) < min(3, limit) and self.calls < self.settings.max_search_calls:
            # Search indexing can miss recent dates. Broaden retrieval only, never verification.
            fallback_start = min(start_date, end_date - timedelta(days=7))
            extra = self._search(query, fallback_start, end_date, limit, "general")
            seen = {s.url for s in found}
            found.extend(s for s in extra if s.url not in seen)
        return found[:limit]

    def _search(self, query, start_date, end_date, limit, topic):
        if self.calls >= self.settings.max_search_calls:
            raise ProviderError("Search call budget exhausted")
        self.calls += 1
        data = {"query": query[:500], "max_results": min(limit, 20), "topic": topic,
                "search_depth": "basic", "include_raw_content": False}
        if topic == "news":
            data["exclude_domains"] = ["instagram.com", "facebook.com", "threads.com", "tiktok.com", "youtube.com"]
        if start_date:
            data["start_date"] = start_date.date().isoformat()
            data["end_date"] = (end_date + timedelta(days=1)).date().isoformat()
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
