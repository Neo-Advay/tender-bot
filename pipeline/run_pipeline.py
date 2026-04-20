# pipeline/run_pipeline.py

import logging
from datetime import datetime, timezone
from core.normalization import normalize_collection
from core.scoring_engine import ScoringEngine
from core.db_manager import DatabaseManager
from pipeline.ingest import ingest_tenders, log_run

logger = logging.getLogger(__name__)
scoring_engine = ScoringEngine()


def run_connector(connector_name: str, client, mapper) -> dict:
    """
    Runs the full pipeline for a single connector.

    Args:
        connector_name: e.g. "TED_EU"
        client:         The connector's client module (must have fetch_notices())
        mapper:         The connector's mapper module (must have map_collection())

    Returns:
        Summary dict with counts
    """
    db = DatabaseManager()
    started_at = datetime.now(timezone.utc)
    summary = {"source": connector_name, "new": 0, "updated": 0, "unchanged": 0, "errors": 0}
    error_msg = None

    try:
        logger.info(f"[Pipeline] Starting run for {connector_name}")

        # Step 1: Fetch raw data
        raw_notices = client.fetch_notices()
        logger.info(f"[Pipeline] Fetched {len(raw_notices)} raw notices from {connector_name}")

        # Step 2: Map to dicts
        mapped = mapper.map_collection(raw_notices)

        # Step 3: Normalize → CanonicalTender objects
        tenders = normalize_collection(mapped)
        logger.info(f"[Pipeline] Normalized {len(tenders)} tenders")

        # Step 4: Score each tender
        tenders = scoring_engine.score_collection(tenders)

        # Step 5: Ingest into DB (insert/update/skip)
        summary, to_notify = ingest_tenders(tenders, db, source=connector_name)

        logger.info(f"[Pipeline] {connector_name} done — {len(to_notify)} tenders queued for notification")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Pipeline] Run failed for {connector_name}: {e}")

    finally:
        # Step 6: Always write run log
        log_run(db, source=connector_name, started_at=started_at, summary=summary, error=error_msg)

    return summary