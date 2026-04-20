# models/tender.py

from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Tender(Base):
    __tablename__ = 'tenders'

    # ── Primary Key ────────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Source identification ──────────────────────────────────────────────────
    source = Column(String(50), nullable=False)          # e.g. "TED_EU"
    external_id = Column(String(100), nullable=False)    # Stable ID from portal

    # ── Core tender fields ─────────────────────────────────────────────────────
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    buyer_name = Column(String(300), default="N/A")
    buyer_country = Column(String(10), default="N/A")
    url = Column(String(1000), default="N/A")

    # ── Dates (stored as ISO strings YYYY-MM-DD) ───────────────────────────────
    publication_date = Column(String(20), nullable=True)
    deadline_date = Column(String(20), nullable=True)

    # ── Classification ─────────────────────────────────────────────────────────
    notice_type = Column(String(100), default="N/A")
    cpv_codes = Column(Text, default="")                 # Comma-separated list

    # ── Scoring ────────────────────────────────────────────────────────────────
    score = Column(Float, default=0.0)
    score_category = Column(String(1), default="C")      # 'A', 'B', or 'C'

    # ── Dedup / update detection ───────────────────────────────────────────────
    content_hash = Column(String(64), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    first_seen_at = Column(String(40), nullable=True)    # When first inserted
    last_seen_at = Column(String(40), nullable=True)     # Last time seen in a run
    last_changed_at = Column(String(40), nullable=True)  # Last time content changed