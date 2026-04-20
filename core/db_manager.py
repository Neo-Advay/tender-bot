# core/db_manager.py

import logging
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.tender import Base, Tender
from core.config_loader import load_config
from models.canonical_tender import CanonicalTender

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        config = load_config()
        db_path = config['database']['path']
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def setup_database(self):
        """Creates all tables based on models."""
        Base.metadata.create_all(self.engine)
        self._create_run_log_table()
        logger.info("Database tables created successfully.")

    # ── Run Log Table ──────────────────────────────────────────────────────────

    def _create_run_log_table(self):
        """Creates the runs_log table if it doesn't exist."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS runs_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    status TEXT,
                    new_count INTEGER DEFAULT 0,
                    updated_count INTEGER DEFAULT 0,
                    unchanged_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    error_summary TEXT
                )
            """))
            conn.commit()

    def insert_run_log(self, run_entry: dict):
        """Inserts a run log entry."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO runs_log 
                (source, started_at, finished_at, status, new_count, updated_count, unchanged_count, error_count, error_summary)
                VALUES (:source, :started_at, :finished_at, :status, :new_count, :updated_count, :unchanged_count, :error_count, :error_summary)
            """), run_entry)
            conn.commit()

    def get_last_successful_run(self, source: str) -> str | None:
        """Returns the started_at timestamp of the last successful run for a source."""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT started_at FROM runs_log
                WHERE source = :source AND status = 'SUCCESS'
                ORDER BY started_at DESC
                LIMIT 1
            """), {"source": source}).fetchone()
        return result[0] if result else None

    # ── Tender CRUD ────────────────────────────────────────────────────────────

    def get_by_external_id(self, source: str, external_id: str) -> Tender | None:
        """Fetch an existing tender by (source, external_id). Returns None if not found."""
        session = self.Session()
        try:
            return session.query(Tender).filter_by(
                source=source,
                external_id=external_id
            ).first()
        finally:
            session.close()

    def insert_tender(self, tender: CanonicalTender):
        """Insert a new tender into the DB."""
        session = self.Session()
        try:
            now = datetime.now(timezone.utc).isoformat()
            db_tender = Tender(
                source=tender.source,
                external_id=tender.external_id,
                title=tender.title,
                description=tender.description,
                buyer_name=tender.buyer_name,
                buyer_country=tender.buyer_country,
                url=tender.url,
                publication_date=tender.publication_date,
                deadline_date=tender.deadline_date,
                notice_type=tender.notice_type,
                cpv_codes=",".join(tender.cpv_codes) if tender.cpv_codes else "",
                score=tender.score,
                score_category=tender.score_category,
                content_hash=tender.content_hash,
                first_seen_at=now,
                last_seen_at=now,
                last_changed_at=now,
            )
            session.add(db_tender)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"[DB] Insert failed for {tender.external_id}: {e}")
            raise
        finally:
            session.close()

    def update_tender(self, tender: CanonicalTender):
        """Update an existing tender's fields and timestamps."""
        session = self.Session()
        try:
            now = datetime.now(timezone.utc).isoformat()
            existing = session.query(Tender).filter_by(
                source=tender.source,
                external_id=tender.external_id
            ).first()

            if existing:
                existing.title = tender.title
                existing.description = tender.description
                existing.buyer_name = tender.buyer_name
                existing.buyer_country = tender.buyer_country
                existing.url = tender.url
                existing.publication_date = tender.publication_date
                existing.deadline_date = tender.deadline_date
                existing.notice_type = tender.notice_type
                existing.cpv_codes = ",".join(tender.cpv_codes) if tender.cpv_codes else ""
                existing.score = tender.score
                existing.score_category = tender.score_category
                existing.content_hash = tender.content_hash
                existing.last_seen_at = now
                existing.last_changed_at = now
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"[DB] Update failed for {tender.external_id}: {e}")
            raise
        finally:
            session.close()