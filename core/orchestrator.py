from typing import List, Dict, Any
import yaml
from pathlib import Path

from core.models import Job, SearchFilters
from core.database import save_jobs, mark_notified, init_db
from core.notifier import notify_all
from sources.remotive import RemotiveSource
from sources.remoteok import RemoteOKSource
from sources.arbeitnow import ArbeitnowSource
from sources.adzuna import AdzunaSource
from sources.companies import CompaniesSource

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"

SOURCES = {
    "remotive": RemotiveSource(),
    "remoteok": RemoteOKSource(),
    "arbeitnow": ArbeitnowSource(),
    "adzuna": AdzunaSource(),
    "companies": CompaniesSource(),
}


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def run_search(filters: SearchFilters) -> Dict[str, Any]:
    """
    Main entry point: fetch from enabled sources, deduplicate, notify.
    Returns summary dict.
    """
    init_db()
    all_jobs: List[Job] = []
    per_source: Dict[str, int] = {}

    enabled = filters.sources or list(SOURCES.keys())

    for name in enabled:
        source = SOURCES.get(name)
        if not source:
            continue
        try:
            jobs = source.fetch(filters)
            per_source[name] = len(jobs)
            all_jobs.extend(jobs)
            print(f"[{name}] fetched {len(jobs)} jobs")
        except Exception as e:
            print(f"[{name}] failed: {e}")
            per_source[name] = 0

    # Deduplicate & persist
    new_jobs = save_jobs(all_jobs)

    # Notify only new ones
    notify_result = {}
    if new_jobs:
        notify_result = notify_all(new_jobs)
        mark_notified([j.id for j in new_jobs])

    return {
        "total_fetched": len(all_jobs),
        "new_jobs": len(new_jobs),
        "per_source": per_source,
        "new_job_list": new_jobs,
        "notifications": notify_result,
    }
