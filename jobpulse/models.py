"""
Pydantic data models for BDJobs API responses.

Provides type-safe data structures for job listings and search results.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .config import BASE_URL


class SearchResult(BaseModel):
    """
    Individual job search result from BDJobs API.

    Represents a single job listing with all relevant details.
    """

    Jobid: str = Field(..., description="Unique job identifier")
    AdType: str = Field(default="0", description="Advertisement type")
    jobTitle: str = Field(..., description="Job title in English")
    companyName: str = Field(..., description="Company/employer name")
    JobTitleBng: str = Field(default="", description="Job title in Bengali")
    deadline: str = Field(default="", description="Application deadline (formatted)")
    deadlineDB: Optional[datetime] = Field(None, description="Application deadline (ISO format)")
    publishDate: Optional[datetime] = Field(None, description="Job posting date")
    eduRec: str = Field(default="", description="Educational requirements")
    experience: str = Field(default="", description="Experience requirements")
    standout: int = Field(default=0, description="Standout job indicator")
    logo: str = Field(default="", description="Company logo URL")
    lantype: int = Field(default=0, description="Language type")
    location: str = Field(default="", description="Job location")
    JobLang: str = Field(default="1", description="Job language")
    jobContext: Optional[str] = Field(None, description="Job context/description")
    isEarlyAccess: bool = Field(default=False, description="Early access job flag")
    OnlineJob: bool = Field(default=False, description="Online/remote job flag")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        str_strip_whitespace = True

    def get_job_url(self) -> str:
        """Generate the job detail URL."""
        return f"{BASE_URL}/jobs/details/{self.Jobid}"

    def is_remote(self) -> bool:
        """Check if this is a remote/online job."""
        return self.OnlineJob


class CommonFilters(BaseModel):
    """Metadata about search results."""

    total_records_found: int = Field(default=0, description="Total number of matching jobs")
    showd: str = Field(default="1", description="Display indicator")
    totalpages: int = Field(default=0, description="Total pages of results")
    total_vacancies: int = Field(default=0, description="Total job vacancies")


class SearchResults(BaseModel):
    """
    Complete search results response from BDJobs API.

    Contains both regular and premium job listings with metadata.
    """

    message: str = Field(..., description="API response message")
    statuscode: str = Field(..., description="API status code")
    data: List[SearchResult] = Field(default_factory=list, description="Regular job listings")
    premiumData: List[SearchResult] = Field(default_factory=list, description="Premium job listings")
    common: CommonFilters = Field(..., description="Search result metadata")

    @property
    def all_jobs(self) -> List[SearchResult]:
        """Get all jobs (regular + premium) combined."""
        return self.data + self.premiumData

    @property
    def total_results(self) -> int:
        """Get total number of results returned."""
        return len(self.data) + len(self.premiumData)

    def is_success(self) -> bool:
        """Check if the API request was successful."""
        return self.statuscode == "1" and self.message.lower() == "success"

    def get_remote_jobs(self) -> List[SearchResult]:
        """Filter and return only remote/online jobs."""
        return [job for job in self.all_jobs if job.is_remote()]
