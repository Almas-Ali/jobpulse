"""
Configuration constants for the JobPulse scraper.
"""

# API Endpoints
BASE_URL = "https://bdjobs.com"
API_BASE_URL = "https://api.bdjobs.com"

# HTTP Client Configuration
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_MIN_WAIT = 1
RETRY_MAX_WAIT = 10

# Rate Limiting
MIN_REQUEST_INTERVAL = 0.5  # seconds between requests

# User Agent
USER_AGENT = "JobPulse/1.0"

# Connection Pool Settings
MAX_CONNECTIONS = 10
MAX_KEEPALIVE_CONNECTIONS = 5
