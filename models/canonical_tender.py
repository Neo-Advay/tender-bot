# core/models/canonical_tender.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CanonicalTender:
    # --- Required fields ---
    source: str                     # e.g. "TED_EU"
    external_id: str                # Stable ID from the source portal
    title: str                      # Tender title (preferably in German)
    url: str                        # Direct link to the notice

    # --- Buyer info ---
    buyer_name: str = "N/A"
    buyer_country: str = "N/A"

    # --- Dates (stored as strings, normalized by normalization.py) ---
    publication_date: Optional[str] = None   # ISO format: YYYY-MM-DD
    deadline_date: Optional[str] = None      # ISO format: YYYY-MM-DD

    # --- Classification ---
    notice_type: str = "N/A"
    cpv_codes: list = field(default_factory=list)

    # --- Content ---
    description: str = ""           # Full text if available

    # --- Scoring (filled later by scoring engine) ---
    score: Optional[float] = None
    score_category: Optional[str] = None     # 'A', 'B', or 'C'

    # --- Audit ---
    raw_payload: Optional[dict] = field(default=None, repr=False)  # Original raw JSON
    content_hash: Optional[str] = None       # Hash for dedup/update detection