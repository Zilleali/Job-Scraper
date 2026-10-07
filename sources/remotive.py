from datetime import datetime
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import Job, SearchFilters
from core.database import make_job_id
from sources.base import BaseSource


class RemotiveSource(BaseSource):
    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch(self, filters: SearchFilters) -> List[Job]:
        jobs: List[Job] = []
        params = {"limit": min(filters.results_per_source, 50)}

        if filters.keywords:
            params["search"] = " ".join(filters.keywords[:3])

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(self.API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            print(f"[Remotive] Fetch error: {e}")
            return []

        for item in data.get("jobs", []):
            title = item.get("title", "")
            company = item.get("company_name", "Unknown")
            url = item.get("url", "")
            description = item.get("description", "") or ""
            category = item.get("category", "")
            tags = item.get("tags", []) or []

            searchable = f"{title} {description} {category}"
            if filters.keywords and not self.matches_keywords(searchable, filters.keywords):
                continue

            posted_at = None
            pub = item.get("publication_date")
            if pub:
                try:
                    posted_at = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except Exception:
                    pass

            job_id = make_job_id(self.name, url, title, company)
            jobs.append(
                Job(
                    id=job_id,
                    title=title,
                    company=company,
                    location="Remote",
                    url=url,
                    source=self.name,
                    description=description[:2000] if description else None,
                    tags=tags if isinstance(tags, list) else [],
                    remote=True,
                    posted_at=posted_at,
                )
            )

            if len(jobs) >= filters.results_per_source:
                break

        return jobs
