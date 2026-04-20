# smoke_test.py
# Run this anytime to verify the pipeline is working correctly.
# Usage: python smoke_test.py

import logging
import sys
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

def run():
    logger.info("=== Smoke Test Starting ===")

    # 1. Check API connectivity
    logger.info("[1] Testing TED API connectivity...")
    from connectors.ted.client import fetch_raw_notices
    notices = fetch_raw_notices(since=None)
    assert len(notices) > 0, "❌ TED API returned 0 notices — check connectivity or query"
    logger.info(f"    ✅ Fetched {len(notices)} raw notices")

    # 2. Check mapper
    logger.info("[2] Testing mapper...")
    from connectors.ted.mapper import map_collection
    mapped = map_collection(notices)
    assert len(mapped) > 0, "❌ Mapper returned 0 results"
    logger.info(f"    ✅ Mapped {len(mapped)} notices")

    # 3. Check normalization
    logger.info("[3] Testing normalization...")
    from core.normalization import normalize_collection
    tenders = normalize_collection(mapped)
    assert len(tenders) > 0, "❌ Normalization returned 0 tenders"
    sample = tenders[0]
    assert sample.external_id, "❌ First tender missing external_id"
    assert sample.title,       "❌ First tender missing title"
    logger.info(f"    ✅ Normalized {len(tenders)} tenders")
    logger.info(f"    Sample: [{sample.score_category}] {sample.title[:60]}...")

    # 4. Check scoring
    logger.info("[4] Testing scoring engine...")
    from core.scoring_engine import ScoringEngine
    scored = ScoringEngine().score_collection(tenders)
    categories = {t.score_category for t in scored}
    logger.info(f"    ✅ Scored {len(scored)} tenders — categories found: {categories}")

    # 5. Check DB connection
    logger.info("[5] Testing DB connection...")
    from core.db_manager import DatabaseManager
    db = DatabaseManager()
    with db.engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("SELECT COUNT(*) FROM tenders")).fetchone()
        logger.info(f"    ✅ DB reachable — {result[0]} tenders in DB")

    logger.info("=== ✅ All smoke tests passed ===")

if __name__ == "__main__":
    run()