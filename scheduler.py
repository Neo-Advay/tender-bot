# scheduler.py

import logging
import time
from datetime import datetime, timezone
from main import run_all

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────
INTERVAL_SECONDS = 60  # Change to 3600 for production (1 hour)


if __name__ == "__main__":
    logger.info("=== Tender Bot Scheduler started ===")
    logger.info(f"    Interval: {INTERVAL_SECONDS} seconds")

    while True:
        run_start = datetime.now(timezone.utc)
        logger.info(f"[Scheduler] Run starting at {run_start.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        try:
            run_all()
        except Exception as e:
            # Scheduler must NEVER crash — log and keep going
            logger.error(f"[Scheduler] Unexpected error: {e}", exc_info=True)

        logger.info(f"[Scheduler] Sleeping for {INTERVAL_SECONDS} seconds...")
        time.sleep(INTERVAL_SECONDS)