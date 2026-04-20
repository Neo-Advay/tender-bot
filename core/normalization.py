# core/normalization.py

import re
import hashlib
import json
import logging
from datetime import datetime
from models.canonical_tender import CanonicalTender

logger = logging.getLogger(__name__)

# ── Date parsing ──────────────────────────────────────────────────────────────

# TED uses YYYYMMDD, others may use DD.MM.YYYY or ISO already
_DATE_FORMATS = [
    "%Y%m%d",       # TED:       20240315
    "%Y-%m-%d",     # ISO:       2024-03-15
    "%d.%m.%Y",     # German:    15.03.2024
    "%d/%m/%Y",     # EU alt:    15/03/2024
]

def parse_date(raw: str | None) -> str | None:
    """Try multiple date formats, return ISO YYYY-MM-DD string or None."""
    if not raw:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            continue
    logger.warning(f"[Normalization] Could not parse date: '{raw}'")
    return None


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str | None) -> str:
    """Strip HTML tags, normalize whitespace."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Content hash ──────────────────────────────────────────────────────────────

def compute_content_hash(tender: CanonicalTender) -> str:
    """
    Hash the key fields of a tender to detect updates.
    If any of these fields change, the hash changes → triggers update notification.
    """
    hash_basis = {
        "title": tender.title,
        "buyer_name": tender.buyer_name,
        "deadline_date": tender.deadline_date,
        "notice_type": tender.notice_type,
        "cpv_codes": sorted(tender.cpv_codes),
    }
    serialized = json.dumps(hash_basis, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ── Main normalization entry point ────────────────────────────────────────────

def normalize(raw_dict: dict) -> CanonicalTender:
    """
    Takes a mapped dict (output of mapper.py) and returns a 
    validated, cleaned CanonicalTender object.
    """
    tender = CanonicalTender(
        source=raw_dict.get("source", "UNKNOWN"),
        external_id=raw_dict.get("external_id", "UNKNOWN"),
        title=clean_text(raw_dict.get("title", "N/A")),
        url=raw_dict.get("url", "N/A"),
        buyer_name=clean_text(raw_dict.get("buyer_name", "N/A")),
        buyer_country=raw_dict.get("buyer_country", "N/A"),
        publication_date=parse_date(raw_dict.get("publication_date")),
        deadline_date=parse_date(raw_dict.get("deadline_date")),
        notice_type=raw_dict.get("notice_type", "N/A"),
        cpv_codes=raw_dict.get("cpv_codes") or [],
        description=clean_text(raw_dict.get("description", "")),
        raw_payload=raw_dict.get("raw_payload"),
    )

    # Compute content hash after all fields are clean
    tender.content_hash = compute_content_hash(tender)

    return tender


def normalize_collection(raw_dicts: list[dict]) -> list[CanonicalTender]:
    """Normalize a list of mapped dicts."""
    results = []
    for raw in raw_dicts:
        try:
            results.append(normalize(raw))
        except Exception as e:
            logger.error(f"[Normalization] Failed for {raw.get('external_id')}: {e}")
    return results