"""
BDJobs Job Search API Client.

A clean, modular interface for searching jobs on BDJobs.
Uses production-ready utilities for HTTP requests, data models, and location handling.
"""

import logging
from typing import Literal
from urllib.parse import quote_plus

from pydantic import ValidationError

from jobpulse.config import API_BASE_URL
from jobpulse.http_client import api_get, close_http_client
from jobpulse.locations import get_city_id
from jobpulse.models import SearchResults

logger = logging.getLogger(__name__)


def build_search_url(
    keyword: str,
    location: str = "",
    page: int = 1,
    results_per_page: int = 50,
    job_type: str = "",
    job_level: str = "",
    age_start: int = 0,
    age_end: int = 0,
    posted_within: str = "",
    salary_start: int = 0,
    salary_end: int = 0,
    experience_start: int = 0,
    experience_end: int = 0,
    is_pro: int = 0,
    is_fresher: bool = False,
    gender: str = "",
    toggle_jobs: bool = True,
    armyp: str = "",
    workplace: str = "",
    facilities_for_pwd: str = "",
) -> str:
    """
    Build the complete search URL with all parameters.

    Args:
        keyword: Job search keyword (required)
        location: Job location
        page: Page number (default: 1)
        results_per_page: Results per page (default: 50)
        job_type: Type of job (FullTime, PartTime, Contract, Intern)
        job_level: Job level (Entry, Mid, Top)
        age_start: Minimum age requirement
        age_end: Maximum age requirement
        posted_within: Days since posting (1-5)
        salary_start: Minimum salary
        salary_end: Maximum salary
        experience_start: Minimum years of experience
        experience_end: Maximum years of experience
        is_pro: Pro jobs flag (0 or 1)
        is_fresher: Fresher jobs only
        gender: Gender filter (M, F, B for both)
        toggle_jobs: Toggle jobs visibility
        armyp: Retired army preferred ("yes" or "")
        workplace: Work from home (1 or "")
        facilities_for_pwd: Facilities for persons with disabilities (1 or "")

    Returns:
        Complete search URL
    """
    # Build age range
    age_range = f"{age_start}/{age_end}" if age_start > 0 or age_end > 0 else ""

    # Build salary range
    salary_range = f"{salary_start}/{salary_end}" if salary_start > 0 or salary_end > 0 else ""

    # Build experience range
    experience_range = f"{experience_start}/{experience_end}" if experience_start > 0 or experience_end > 0 else ""

    # Convert location name to ID, handle None case
    location_id = get_city_id(location) if location else None
    location_param = location_id if location_id is not None else ""

    # Build URL with all parameters
    search_url = (
        f"{API_BASE_URL}/Jobs/api/JobSearch/GetJobSearch?"
        f"Icat=&"
        f"industry=&"
        f"category=&"
        f"org=&"
        f"jobNature=&"
        f"Fcat=&"
        f"location={location_param}&"
        f"Qot=&"
        f"jobType={quote_plus(job_type)}&"
        f"jobLevel={quote_plus(job_level)}&"
        f"postedWithin={posted_within}&"
        f"deadline=&"
        f"keyword={quote_plus(keyword)}&"
        f"pg={page}&"
        f"qAge={age_range}&"
        f"Salary={salary_range}&"
        f"experience={experience_range}&"
        f"gender={gender}&"
        f"MExp=&"
        f"genderB=&"
        f"MPostings=&"
        f"MCat=&"
        f"version=&"
        f"rpp={results_per_page}&"
        f"Newspaper=&"
        f"armyp={armyp}&"
        f"QDisablePerson=&"
        f"pwd=&"
        f"workplace={workplace}&"
        f"facilitiesForPWD={facilities_for_pwd}&"
        f"SaveFilterList=&"
        f"UserFilterName=&"
        f"HUserFilterName=&"
        f"earlyJobAccess=&"
        f"isPro={is_pro}&"
        f"ToggleJobs={'true' if toggle_jobs else 'false'}&"
        f"isFresher={'true' if is_fresher else 'false'}"
    )

    return search_url


def search_jobs(
    keyword: str,
    location: str = "",
    page: int = 1,
    results_per_page: int = 50,
    job_type: Literal["", "FullTime", "PartTime", "Contract", "Intern"] = "",
    job_level: Literal["", "Entry", "Mid", "Top"] = "",
    age_start: int = 0,
    age_end: int = 0,
    posted_within: Literal["", "1", "2", "3", "4", "5"] = "",
    salary_start: int = 0,
    salary_end: int = 0,
    experience_start: int = 0,
    experience_end: int = 0,
    is_pro: int = 0,
    is_fresher: bool = False,
    gender: Literal["", "M", "F", "B"] = "",
    toggle_jobs: bool = True,
    armyp: Literal["", "yes"] = "",
    workplace: Literal["", "1"] = "",
    facilities_for_pwd: Literal["", "1"] = "",
) -> SearchResults:
    """
    Search for jobs based on keyword and filters using the BDJobs API.

    Args:
        keyword: Job search keyword (required)
        location: Job location
        page: Page number (default: 1)
        results_per_page: Results per page (default: 50)
        job_type: Type of job (FullTime, PartTime, Contract, Intern)
        job_level: Job level (Entry, Mid, Top)
        age_start: Minimum age requirement
        age_end: Maximum age requirement
        posted_within: Days since posting (1=Today, 2=Last 2 days, etc.)
        salary_start: Minimum salary
        salary_end: Maximum salary
        experience_start: Minimum years of experience
        experience_end: Maximum years of experience
        is_pro: Pro jobs flag (0 or 1)
        is_fresher: Fresher jobs only
        gender: Gender filter (M=Male, F=Female, B=Both)
        toggle_jobs: Toggle jobs visibility
        armyp: Retired army preferred ("yes" or "")
        workplace: Work from home (1 or "")
        facilities_for_pwd: Facilities for persons with disabilities (1 or "")

    Returns:
        SearchResults object containing job listings and metadata

    Raises:
        ValueError: If keyword is empty or invalid parameters
        RuntimeError: If API request fails
        ValidationError: If API response doesn't match expected format
    """
    # Validate required parameters
    if not keyword or not keyword.strip():
        raise ValueError("Keyword parameter is required and cannot be empty")

    # Validate page number
    if page < 1:
        raise ValueError("Page number must be >= 1")

    # Validate results per page
    if results_per_page < 1 or results_per_page > 100:
        raise ValueError("Results per page must be between 1 and 100")

    # Build and execute search
    try:
        search_url = build_search_url(
            keyword=keyword,
            location=location,
            page=page,
            results_per_page=results_per_page,
            job_type=job_type,
            job_level=job_level,
            age_start=age_start,
            age_end=age_end,
            posted_within=posted_within,
            salary_start=salary_start,
            salary_end=salary_end,
            experience_start=experience_start,
            experience_end=experience_end,
            is_pro=is_pro,
            is_fresher=is_fresher,
            gender=gender,
            toggle_jobs=toggle_jobs,
            armyp=armyp,
            workplace=workplace,
            facilities_for_pwd=facilities_for_pwd,
        )

        logger.info(f"Searching jobs with keyword='{keyword}', location='{location}', page={page}")

        response_data = api_get(search_url)

        # Parse and validate response
        try:
            results = SearchResults(**response_data)

            if not results.is_success():
                logger.warning(f"API returned non-success status: {results.message}")

            logger.info(f"Found {results.total_results} jobs (Total available: {results.common.total_records_found})")

            return results

        except ValidationError as e:
            logger.error(f"Failed to parse API response: {e}")
            raise ValueError(f"Invalid API response format: {e}")

    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise


# Re-export commonly used items
__all__ = [
    "search_jobs",
    "build_search_url",
    "close_http_client",
]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        print("=" * 70)
        print("BDJobs Job Search Example")
        print("=" * 70)

        results = search_jobs(keyword="software engineer", location="Dhaka", results_per_page=5)

        print(f"\nTotal jobs found: {results.common.total_records_found}")
        print(f"Jobs in this page: {results.total_results}\n")

        for i, job in enumerate(results.all_jobs, 1):
            print(f"{i}. {job.jobTitle}")
            print(f"   Company: {job.companyName}")
            print(f"   Location: {job.location}")
            print(f"   Deadline: {job.deadline}")
            print(f"   URL: {job.get_job_url()}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Error in example")
    finally:
        close_http_client()
        print("=" * 70)
