# pipeline/run_pipeline.py

import logging
from datetime import datetime, timezone
from core.normalization import normalize_collection
from core.scoring_engine import ScoringEngine
from core.db_manager import DatabaseManager
from pipeline.ingest import ingest_tenders, log_run
from pipeline.notifications import NotificationService

logger = logging.getLogger(__name__)
scoring_engine = ScoringEngine()
notification_service = NotificationService(mode="smtp")

def _check_tender_quality(tenders, source):
    """Logs warnings for tenders missing critical fields."""
    issues = 0
    for t in tenders:
        missing = []
        if not t.external_id:   missing.append("external_id")
        if not t.title:         missing.append("title")
        if not t.publication_date: missing.append("publication_date")
        if not t.source:        missing.append("source")
        if missing:
            logger.warning(f"[QC] {source} — tender {t.external_id or '?'} missing fields: {missing}")
            issues += 1
    if issues:
        logger.warning(f"[QC] {source} — {issues}/{len(tenders)} tenders had quality issues")
    else:
        logger.info(f"[QC] {source} — all {len(tenders)} tenders passed quality check OK")

def _check_fetch_health(notices, source, since):
    """Warns if fetch returns suspiciously low results."""
    if since is None and len(notices) == 0:
        logger.error(f"[HealthCheck] {source} — Full fetch returned 0 results. API may be down or query broken!")
    elif len(notices) == 0:
        logger.info(f"[HealthCheck] {source} — 0 new notices since {since.date()}. Normal if no new tenders today.")
    else:
        logger.info(f"[HealthCheck] {source} — Fetch healthy: {len(notices)} notices returned.")

def run_connector(connector_name: str, client, mapper) -> dict:
    """
    Runs the full pipeline for a single connector.

    Args:
        connector_name: e.g. "TED_EU"
        client:         The connector's client module (must have fetch_raw_notices())
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
        raw_notices = []
        since = db.get_last_run_time(source=connector_name)

              
        raw_notices = client.fetch_raw_notices(since = since)
        logger.info(f"[Pipeline] Fetched {len(raw_notices)} raw notices from {connector_name}")

        # Step 1b: Fetch health check
        _check_fetch_health(raw_notices, connector_name, since)

        # Step 2: Map to dicts
        mapped = mapper.map_collection(raw_notices)

        # Step 3: Normalize → CanonicalTender objects
        tenders = normalize_collection(mapped)
        logger.info(f"[Pipeline] Normalized {len(tenders)} tenders")

        # Step 3b: Data quality checks
        _check_tender_quality(tenders, connector_name)

        # Step 4: Score each tender
        tenders = scoring_engine.score_collection(tenders)

        # Step 5: Ingest into DB (insert/update/skip)
        summary, to_notify = ingest_tenders(tenders, db, source=connector_name)

        logger.info(f"[Pipeline] {connector_name} done — {len(to_notify)} tenders queued for notification")
        notification_service.notify(to_notify, source=connector_name,db=db)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Pipeline] Run failed for {connector_name}: {e}")

    finally:
        # Step 6: Always write run log
        log_run(db, source=connector_name, started_at=started_at, summary=summary, error=error_msg)

    return summary