import os
from datetime import datetime
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from core.models import Job, SearchFilters
from core.database import make_job_id
from sources.base import BaseSource

load_dotenv()


class AdzunaSource(BaseSource):
    name = "adzuna"
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch(self, filters: SearchFilters) -> List[Job]:
        if not self.is_configured:
            print("[Adzuna] Skipping – ADZUNA_APP_ID / ADZUNA_APP_KEY not set")
            return []

        jobs: List[Job] = []
        countries = filters.countries or os.getenv("ADZUNA_COUNTRIES", "us,gb").split(",")
        countries = [c.strip().lower() for c in countries if c.strip()]

        what = " ".join(filters.keywords[:4]) if filters.keywords else "network engineer"
        where = filters.locations[0] if filters.locations else ""

        for country in countries[:3]:
            page = 1
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": min(filters.results_per_source, 20),
                "what": what,
                "content-type": "application/json",
            }
            if where:
                params["where"] = where

            url = f"{self.BASE_URL}/{country}/search/{page}"

            try:
                with httpx.Client(timeout=20) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as e:
                print(f"[Adzuna] Error for {country}: {e}")
                continue

            for item in data.get("results", []):
                title = item.get("title", "")
                company = (item.get("company") or {}).get("display_name", "Unknown")
                loc = (item.get("location") or {}).get("display_name", country.upper())
                job_url = item.get("redirect_url") or item.get("url") or ""
                description = item.get("description", "") or ""

                salary = None
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                if salary_min or salary_max:
                    parts = []
                    if salary_min:
                        parts.append(f"{int(salary_min):,}")
                    if salary_max:
                        parts.append(f"{int(salary_max):,}")
                    salary = " - ".join(parts)

                posted_at = None
                created = item.get("created")
                if created:
                    try:
                        posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    except Exception:
                        pass

                remote = "remote" in loc.lower() or "remote" in title.lower()

                if filters.remote_only and not remote:
                    continue

                job_id = make_job_id(self.name, job_url, title, company)
                jobs.append(
                    Job(
                        id=job_id,
                        title=title,
                        company=company,
                        location=loc,
                        url=job_url,
                        source=self.name,
                        description=description[:2000] if description else None,
                        salary=salary,
                        salary_min=float(salary_min) if salary_min else None,
                        salary_max=float(salary_max) if salary_max else None,
                        remote=remote,
                        posted_at=posted_at,
                    )
                )

                if len(jobs) >= filters.results_per_source:
                    return jobs

        return jobs
