from datetime import datetime
from pathlib import Path
from typing import List, Optional
import hashlib

from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, Float, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from core.models import Job

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "jobs.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class JobRecord(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)          # our unique id
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, default="Remote")
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    salary = Column(String, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    tags = Column(String, nullable=True)           # comma-separated
    remote = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    first_seen = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def make_job_id(source: str, url: str, title: str, company: str) -> str:
    """Create a stable unique ID for deduplication."""
    raw = f"{source}|{url}|{title}|{company}".lower().strip()
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def job_exists(session: Session, job_id: str) -> bool:
    return session.query(JobRecord).filter(JobRecord.id == job_id).first() is not None


def save_jobs(jobs: List[Job]) -> List[Job]:
    """
    Save new jobs only. Returns the list of truly new jobs.
    """
    init_db()
    new_jobs: List[Job] = []
    session = get_session()
    try:
        for job in jobs:
            if not job.id:
                job.id = make_job_id(job.source, job.url, job.title, job.company)

            if job_exists(session, job.id):
                continue

            record = JobRecord(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                url=job.url,
                source=job.source,
                description=job.description,
                salary=job.salary,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                tags=",".join(job.tags) if job.tags else None,
                remote=job.remote,
                posted_at=job.posted_at,
                scraped_at=job.scraped_at,
                first_seen=datetime.utcnow(),
                notified=False,
            )
            session.add(record)
            new_jobs.append(job)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return new_jobs


def mark_notified(job_ids: List[str]) -> None:
    session = get_session()
    try:
        session.query(JobRecord).filter(JobRecord.id.in_(job_ids)).update(
            {JobRecord.notified: True}, synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


def get_all_jobs(limit: int = 500) -> List[JobRecord]:
    session = get_session()
    try:
        return (
            session.query(JobRecord)
            .order_by(JobRecord.first_seen.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def get_new_unnotified() -> List[JobRecord]:
    session = get_session()
    try:
        return session.query(JobRecord).filter(JobRecord.notified == False).all()
    finally:
        session.close()
