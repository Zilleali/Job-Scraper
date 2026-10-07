from pathlib import Path
from typing import List
import pandas as pd
from datetime import datetime

from core.database import get_all_jobs, JobRecord

BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = BASE_DIR / "data"


def jobs_to_dataframe(records: List[JobRecord] | None = None) -> pd.DataFrame:
    if records is None:
        records = get_all_jobs(limit=2000)

    rows = []
    for r in records:
        rows.append({
            "Title": r.title,
            "Company": r.company,
            "Location": r.location,
            "Remote": r.remote,
            "Salary": r.salary or "",
            "Source": r.source,
            "URL": r.url,
            "Tags": r.tags or "",
            "Posted At": r.posted_at,
            "First Seen": r.first_seen,
            "Notified": r.notified,
        })
    return pd.DataFrame(rows)


def export_csv(filename: str | None = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = EXPORT_DIR / filename
    df = jobs_to_dataframe()
    df.to_csv(path, index=False)
    return path


def export_excel(filename: str | None = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = EXPORT_DIR / filename
    df = jobs_to_dataframe()
    df.to_excel(path, index=False, engine="openpyxl")
    return path
