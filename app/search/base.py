from abc import ABC, abstractmethod
from datetime import datetime
from app.models import NewsSource


class SearchProvider(ABC):
    def discover(self, query: str, start_date: datetime, end_date: datetime, limit: int) -> list[NewsSource]:
        """Recent-news retrieval; confirmation still requires fetched page evidence."""
        return self.search(query, start_date, end_date, limit)

    @abstractmethod
    def search(self, query: str, start_date: datetime | None, end_date: datetime, limit: int) -> list[NewsSource]:
        """Discovery only: search dates are not publication evidence."""


class PageProvider(ABC):
    @abstractmethod
    def fetch(self, source: NewsSource) -> NewsSource:
        """Fetch and extract a public article, including publication evidence."""
