"""
JobPulse - A web scraping tool for job listings.
Specifically designed to extract job postings from BDJobs.com portal.

Modular, production-ready interface with:
- Automatic retries and connection pooling
- Type-safe data models
- Comprehensive error handling
"""

__author__ = "Md. Almas Ali"
__version__ = "1.0.0"
__license__ = "MIT"
__copyright__ = "Copyright 2024, Md. Almas Ali"

# Import main API
from .http_client import close_http_client, http_client_context
from .locations import (
    get_all_cities,
    get_city_id,
    get_city_name,
    search_cities,
)
from .models import CommonFilters, SearchResult, SearchResults
from .scraper import build_search_url, search_jobs

__all__ = [
    # Main search functions
    "search_jobs",
    "build_search_url",
    # HTTP client management
    "close_http_client",
    "http_client_context",
    # Location utilities
    "get_city_id",
    "get_city_name",
    "get_all_cities",
    "search_cities",
    # Data models
    "SearchResult",
    "SearchResults",
    "CommonFilters",
]
