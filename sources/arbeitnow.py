from datetime import datetime
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import Job, SearchFilters
from core.database import make_job_id
from sources.base import BaseSource


class ArbeitnowSource(BaseSource):
    name = "arbeitnow"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch(self, filters: SearchFilters) -> List[Job]:
        jobs: List[Job] = []

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(self.API_URL)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            print(f"[Arbeitnow] Fetch error: {e}")
            return []

        items = data.get("data", []) if isinstance(data, dict) else data

        for item in items:
            title = item.get("title", "")
            company = item.get("company_name", "Unknown")
            url = item.get("url", "")
            location = item.get("location", "Remote")
            description = item.get("description", "") or ""
            tags = item.get("tags", []) or []
            remote = item.get("remote", False)
            if isinstance(remote, str):
                remote = remote.lower() in ("true", "1", "yes", "remote")

            searchable = f"{title} {description} {location}"
            if filters.keywords and not self.matches_keywords(searchable, filters.keywords):
                continue

            if filters.remote_only and not remote and "remote" not in location.lower():
                continue

            posted_at = None
            created = item.get("created_at") or item.get("date")
            if created:
                try:
                    posted_at = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                except Exception:
                    pass

            job_id = make_job_id(self.name, url, title, company)
            jobs.append(
                Job(
                    id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    source=self.name,
                    description=description[:2000] if description else None,
                    tags=tags if isinstance(tags, list) else [],
                    remote=bool(remote) or "remote" in location.lower(),
                    posted_at=posted_at,
                )
            )

            if len(jobs) >= filters.results_per_source:
                break

        return jobs
