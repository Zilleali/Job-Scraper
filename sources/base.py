from abc import ABC, abstractmethod
from typing import List
from core.models import Job, SearchFilters


class BaseSource(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, filters: SearchFilters) -> List[Job]:
        """Fetch jobs matching the given filters."""
        pass

    def matches_keywords(self, text: str, keywords: List[str]) -> bool:
        if not keywords:
            return True
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
