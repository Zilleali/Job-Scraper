from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class Job(BaseModel):
    """Normalized job schema used across all sources."""
    id: str = Field(..., description="Unique ID (source + original id or hash)")
    title: str
    company: str
    location: str = "Remote"
    url: str
    source: str
    description: Optional[str] = None
    salary: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    remote: bool = False
    posted_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class SearchFilters(BaseModel):
    """User search filters coming from the dashboard or config."""
    keywords: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    countries: List[str] = Field(default_factory=list)
    remote_only: bool = False
    results_per_source: int = 30
    sources: List[str] = Field(default_factory=lambda: ["remotive", "remoteok", "arbeitnow"])
