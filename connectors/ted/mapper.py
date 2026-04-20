# connectors/ted/mapper.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def map_to_canonical(raw_notice: dict) -> dict:
    """
    Maps a single raw TED notice dictionary to a flat dictionary 
    matching our CanonicalTender schema.
    """
    
    # 1. Extract External ID (Stable ID from TED)
    # TED uses 'publication-number' e.g., '123456-2024'
    external_id = raw_notice.get('publication-number', 'UNKNOWN')

    # 2. Handle Multilingual Title
    # Fallback order: German -> English -> first available -> 'N/A'
    title_dict = raw_notice.get('notice-title', {})
    title = (
        title_dict.get('deu') or 
        title_dict.get('eng') or 
        next(iter(title_dict.values()), "N/A")
    )

    # 3. Buyer Mapping
    # TED buyers are a dict of translations; we pick the first one available
    buyer_data = raw_notice.get('buyer-name', {})
    buyer_name = "N/A"
    if buyer_data:
        # TED structure: {"deu": ["Name"], "eng": ["Name"]}
        names = next(iter(buyer_data.values()), [])
        if names:
            buyer_name = names[0]

    # 4. Country Mapping
    # Returns a list, e.g., ['DEU']
    countries = raw_notice.get('buyer-country', [])
    country = countries[0] if countries else "N/A"

    # 5. Link Mapping
    # We prefer the English HTML link if possible
    links = raw_notice.get('links', {}).get('html', {})
    url = links.get('ENG') or links.get('DEU') or next(iter(links.values()), "N/A")

    # 6. Dates (TED uses YYYYMMDD string format)
    pub_date_raw = raw_notice.get('publication-date')
    deadline_raw = raw_notice.get('deadline-receipt-tenders')

    # 7. CPV Codes
    # TED returns a list of codes
    cpv_codes = raw_notice.get('cpv-code', [])

    # Construct the canonical dictionary
    canonical = {
        "source": "TED_EU",
        "external_id": external_id,
        "title": title,
        "description": "",  # Search API often doesn't give full text; handle in enricher later
        "buyer_name": buyer_name,
        "buyer_country": country,
        "url": url,
        "publication_date": pub_date_raw,  # Pass raw for now; normalization info follows
        "deadline_date": deadline_raw,
        "notice_type": raw_notice.get('notice-type', 'N/A'),
        "cpv_codes": cpv_codes,
        "raw_payload": raw_notice  # Keep original for auditing
    }

    return canonical

def map_collection(raw_notices: list[dict]) -> list[dict]:
    """Helper to map a whole list of notices."""
    mapped = []
    for raw in raw_notices:
        try:
            mapped.append(map_to_canonical(raw))
        except Exception as e:
            logger.error(f"[TED] Mapping failed for notice {raw.get('publication-number')}: {e}")
    return mapped