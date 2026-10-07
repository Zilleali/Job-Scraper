from datetime import datetime
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import Job, SearchFilters
from core.database import make_job_id
from sources.base import BaseSource


class RemoteOKSource(BaseSource):
    name = "remoteok"
    API_URL = "https://remoteok.com/api"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch(self, filters: SearchFilters) -> List[Job]:
        jobs: List[Job] = []

        headers = {
            "User-Agent": "JobMonitor/1.0 (personal use)"
        }

        try:
            with httpx.Client(timeout=20, headers=headers) as client:
                resp = client.get(self.API_URL)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            print(f"[RemoteOK] Fetch error: {e}")
            return []

        items = data[1:] if data and isinstance(data, list) else []

        for item in items:
            if not isinstance(item, dict):
                continue

            title = item.get("position") or item.get("title") or ""
            company = item.get("company") or "Unknown"
            url = item.get("url") or item.get("apply_url") or ""
            if url and not url.startswith("http"):
                url = f"https://remoteok.com{url}"

            description = item.get("description") or ""
            tags = item.get("tags") or []
            location = item.get("location") or "Remote"

            searchable = f"{title} {description} {' '.join(tags)}"
            if filters.keywords and not self.matches_keywords(searchable, filters.keywords):
                continue

            salary = None
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            if salary_min or salary_max:
                parts = []
                if salary_min:
                    parts.append(f"${int(salary_min):,}")
                if salary_max:
                    parts.append(f"${int(salary_max):,}")
                salary = " - ".join(parts)

            posted_at = None
            epoch = item.get("epoch") or item.get("date")
            if epoch:
                try:
                    posted_at = datetime.utcfromtimestamp(int(epoch))
                except Exception:
                    pass

            job_id = make_job_id(self.name, url, title, company)
            jobs.append(
                Job(
                    id=job_id,
                    title=title,
                    company=company,
                    location=location or "Remote",
                    url=url,
                    source=self.name,
                    description=description[:2000] if description else None,
                    salary=salary,
                    salary_min=float(salary_min) if salary_min else None,
                    salary_max=float(salary_max) if salary_max else None,
                    tags=tags if isinstance(tags, list) else [],
                    remote=True,
                    posted_at=posted_at,
                )
            )

            if len(jobs) >= filters.results_per_source:
                break

        return jobs
