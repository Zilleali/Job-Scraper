"""
Company career pages via public Greenhouse & Lever APIs.
No authentication required.
"""
from datetime import datetime
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import Job, SearchFilters
from core.database import make_job_id
from sources.base import BaseSource


# Curated boards that often hire Network / NOC / IT / Infrastructure roles
KNOWN_BOARDS = [
    {"name": "Cloudflare", "type": "greenhouse", "token": "cloudflare"},
    {"name": "Stripe", "type": "greenhouse", "token": "stripe"},
    {"name": "Discord", "type": "greenhouse", "token": "discord"},
    {"name": "Airbnb", "type": "greenhouse", "token": "airbnb"},
    {"name": "Coinbase", "type": "greenhouse", "token": "coinbase"},
    {"name": "Robinhood", "type": "greenhouse", "token": "robinhood"},
    {"name": "DoorDash", "type": "greenhouse", "token": "doordash"},
    {"name": "Notion", "type": "greenhouse", "token": "notion"},
    {"name": "Figma", "type": "greenhouse", "token": "figma"},
    {"name": "Vercel", "type": "greenhouse", "token": "vercel"},
    {"name": "Linear", "type": "greenhouse", "token": "linear"},
    {"name": "Anthropic", "type": "greenhouse", "token": "anthropic"},
    {"name": "Plaid", "type": "greenhouse", "token": "plaid"},
    {"name": "Rippling", "type": "greenhouse", "token": "rippling"},
    {"name": "Gusto", "type": "greenhouse", "token": "gusto"},
    {"name": "Asana", "type": "greenhouse", "token": "asana"},
    {"name": "Databricks", "type": "greenhouse", "token": "databricks"},
    {"name": "Scale AI", "type": "greenhouse", "token": "scaleai"},
    {"name": "Anduril", "type": "greenhouse", "token": "andurilindustries"},
    {"name": "SpaceX", "type": "greenhouse", "token": "spacex"},
    {"name": "Netflix", "type": "lever", "token": "netflix"},
    {"name": "Spotify", "type": "lever", "token": "spotify"},
    {"name": "Palantir", "type": "lever", "token": "palantir"},
    {"name": "Twitch", "type": "lever", "token": "twitch"},
    {"name": "Shopify", "type": "lever", "token": "shopify"},
]


class CompaniesSource(BaseSource):
    name = "companies"

    def __init__(self, boards: list | None = None):
        self.boards = boards or KNOWN_BOARDS

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    def _fetch_greenhouse(self, token: str, company_name: str) -> List[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
        params = {"content": "true"}
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(url, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return data.get("jobs", [])
        except Exception as e:
            print(f"[Companies/GH {company_name}] {e}")
            return []

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    def _fetch_lever(self, token: str, company_name: str) -> List[dict]:
        url = f"https://api.lever.co/v0/postings/{token}"
        params = {"mode": "json"}
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(url, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[Companies/Lever {company_name}] {e}")
            return []

    def fetch(self, filters: SearchFilters) -> List[Job]:
        jobs: List[Job] = []
        limit = filters.results_per_source or 30

        for board in self.boards:
            if len(jobs) >= limit:
                break

            company_name = board["name"]
            token = board["token"]
            btype = board["type"]

            raw_items: List[dict] = []
            if btype == "greenhouse":
                raw_items = self._fetch_greenhouse(token, company_name)
            elif btype == "lever":
                raw_items = self._fetch_lever(token, company_name)

            for item in raw_items:
                if btype == "greenhouse":
                    title = item.get("title", "")
                    loc_obj = item.get("location") or {}
                    location = loc_obj.get("name", "Remote") if isinstance(loc_obj, dict) else str(loc_obj)
                    url = item.get("absolute_url") or ""
                    description = item.get("content") or ""
                    if description and "<" in description:
                        description = description[:500]
                else:
                    title = item.get("text") or item.get("title") or ""
                    cats = item.get("categories") or {}
                    location = cats.get("location") or item.get("country") or "Remote"
                    url = item.get("hostedUrl") or item.get("applyUrl") or ""
                    description = item.get("descriptionPlain") or item.get("description") or ""

                searchable = f"{title} {location} {description}"
                if filters.keywords and not self.matches_keywords(searchable, filters.keywords):
                    continue

                remote = (
                    "remote" in location.lower()
                    or "remote" in title.lower()
                    or location.lower() in ("worldwide", "anywhere")
                )

                if filters.remote_only and not remote:
                    continue

                job_id = make_job_id(self.name, url, title, company_name)
                jobs.append(
                    Job(
                        id=job_id,
                        title=title,
                        company=company_name,
                        location=location or "Remote",
                        url=url,
                        source=f"{self.name}:{btype}",
                        description=description[:2000] if description else None,
                        remote=remote,
                    )
                )

                if len(jobs) >= limit:
                    break

        return jobs
