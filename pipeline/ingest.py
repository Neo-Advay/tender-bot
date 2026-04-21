# pipeline/ingest.py

import logging
from datetime import datetime, timezone
from typing import Optional
from models.canonical_tender import CanonicalTender

logger = logging.getLogger(__name__)


def ingest_tenders(
    tenders: list[CanonicalTender],
    db_manager,
    source: str,
) -> dict:
    """
    Core ingestion logic. For each canonical tender:
      - NEW:       insert into DB, mark for notification
      - UPDATED:   update DB record, mark for notification
      - UNCHANGED: skip

    Args:
        tenders:    List of normalized CanonicalTender objects
        db_manager: Instance of DatabaseManager
        source:     Portal name e.g. "TED_EU" (for logging/run log)

    Returns:
        Summary dict with counts: new, updated, unchanged, errors
    """
    summary = {"source": source, "new": 0, "updated": 0, "unchanged": 0, "errors": 0}
    to_notify = []  # Tenders that need a notification (new or updated)

    for tender in tenders:
        try:
            existing = db_manager.get_by_external_id(tender.source, tender.external_id)

            if existing is None:
                # ── NEW tender ──────────────────────────────────────────
                db_manager.insert_tender(tender)
                tender._is_new = True
                to_notify.append((tender, "NEW"))
                summary["new"] += 1
                logger.info(f"[Ingest] NEW: [{source}] {tender.external_id} — {tender.title[:60]}")

            elif existing.content_hash != tender.content_hash:
                # ── UPDATED tender ──────────────────────────────────────
                db_manager.update_tender(tender)
                tender._is_new = False
                to_notify.append((tender, "UPDATED"))
                summary["updated"] += 1
                logger.info(f"[Ingest] UPDATED: [{source}] {tender.external_id} — {tender.title[:60]}")

            else:
                # ── UNCHANGED tender ────────────────────────────────────
                summary["unchanged"] += 1
                logger.debug(f"[Ingest] UNCHANGED: [{source}] {tender.external_id}")

        except Exception as e:
            summary["errors"] += 1
            logger.error(f"[Ingest] Error processing {tender.external_id}: {e}")

    logger.info(
        f"[Ingest] Run complete for {source} — "
        f"New: {summary['new']}, Updated: {summary['updated']}, "
        f"Unchanged: {summary['unchanged']}, Errors: {summary['errors']}"
    )

    return summary, to_notify


def log_run(
    db_manager,
    source: str,
    started_at: datetime,
    summary: dict,
    error: Optional[str] = None,
):
    """
    Writes a run log entry to the DB after each connector run.

    Args:
        db_manager:  Instance of DatabaseManager
        source:      Portal name e.g. "TED_EU"
        started_at:  When the run started
        summary:     Output dict from ingest_tenders()
        error:       Optional error message if the run failed entirely
    """
    finished_at = datetime.now(timezone.utc)
    status = "SUCCESS" if not error else "FAILED"

    run_entry = {
        "source": source,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "status": status,
        "new_count": summary.get("new", 0),
        "updated_count": summary.get("updated", 0),
        "unchanged_count": summary.get("unchanged", 0),
        "error_count": summary.get("errors", 0),
        "error_summary": error,
    }

    try:
        db_manager.insert_run_log(run_entry)
        logger.info(f"[Ingest] Run log saved for {source} — Status: {status}")
    except Exception as e:
        logger.error(f"[Ingest] Failed to save run log for {source}: {e}")