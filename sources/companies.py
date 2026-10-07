"""
Basic company career page support.
Currently a placeholder that can be expanded with Greenhouse / Lever board tokens.
"""
from typing import List
from core.models import Job, SearchFilters
from sources.base import BaseSource


class CompaniesSource(BaseSource):
    name = "companies"

    KNOWN_BOARDS = {
        # "stripe": {"type": "greenhouse", "token": "stripe"},
        # "cloudflare": {"type": "greenhouse", "token": "cloudflare"},
    }

    def fetch(self, filters: SearchFilters) -> List[Job]:
        print("[Companies] No boards configured yet – skipping")
        return []
