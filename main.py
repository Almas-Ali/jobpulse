"""
JobPulse - Main Entry Point
A production-ready job search application for BDJobs with GUI and database support.
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("jobpulse.log")],
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        from jobpulse.gui import run_application

        logger.info("Starting JobPulse application...")
        run_application()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
