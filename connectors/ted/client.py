# connectors/ted/client.py
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import logging
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

FIELDS = [
    "publication-number",
    "publication-date",
    "notice-title",
    "buyer-name",
    "buyer-country",
    "notice-type",
    "links",
]

MAX_PAGES = 5
PAGE_SIZE = 100
REQUEST_TIMEOUT = (5, 30)       # (connect timeout, read timeout) in seconds
MAX_RETRIES = 3
BACKOFF_BASE = 2                # seconds


def _build_query(since: Optional[datetime]) -> str:
    """Build the TED expert query string."""
    base_query = 'FT ~ "messebau"'
    if since:
        date_str = since.strftime("%Y%m%d")
        return f'({base_query}) AND (PD >= {date_str})'
    return base_query


def _post_with_retry(payload: dict) -> dict:
    """POST to TED search API with retries and exponential backoff."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                TED_SEARCH_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                verify=False,
            )

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", BACKOFF_BASE * attempt))
                logger.warning(f"[TED] Rate limited. Waiting {retry_after}s before retry {attempt}/{MAX_RETRIES}.")
                time.sleep(retry_after)

            elif response.status_code in (500, 502, 503, 504):
                wait = BACKOFF_BASE ** attempt
                logger.warning(f"[TED] Server error {response.status_code}. Retrying in {wait}s (attempt {attempt}/{MAX_RETRIES}).")
                time.sleep(wait)

            else:
                logger.error(f"[TED] Unrecoverable HTTP {response.status_code}: {response.text[:300]}")
                raise RuntimeError(f"TED API returned HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            wait = BACKOFF_BASE ** attempt
            logger.warning(f"[TED] Request timed out. Retrying in {wait}s (attempt {attempt}/{MAX_RETRIES}).")
            time.sleep(wait)

        except requests.exceptions.ConnectionError as e:
            wait = BACKOFF_BASE ** attempt
            logger.warning(f"[TED] Connection error: {e}. Retrying in {wait}s (attempt {attempt}/{MAX_RETRIES}).")
            time.sleep(wait)

    raise RuntimeError(f"[TED] All {MAX_RETRIES} retry attempts failed.")


def fetch_raw_notices(since: Optional[datetime] = None) -> list[dict]:
    """
    Fetch raw notice dicts from TED API.

    Args:
        since: If provided, filters notices published on or after this date.

    Returns:
        List of raw notice dicts as returned by TED API.
    """
    query = _build_query(since)
    all_notices = []

    for page in range(1, MAX_PAGES + 1):
        payload = {
            "query": query,
            "scope": "ACTIVE",
            "limit": PAGE_SIZE,
            "page": page,
            "paginationMode": "PAGE_NUMBER",
            "checkQuerySyntax": False,
            "fields": FIELDS,
            "onlyLatestVersions": True,
        }
        
        
        logger.info(f"[TED] Fetching page {page} (since={since.date() if since else 'all'})...")

        try:
            data = _post_with_retry(payload)
        except RuntimeError as e:
            logger.error(f"[TED] Aborting fetch at page {page}: {e}")
            break

        notices = data.get("notices", [])
        logger.info(f"[TED] Page {page}: {len(notices)} notices returned.")
        all_notices.extend(notices)

        # Stop early if fewer results than page size (last page)
        if len(notices) < PAGE_SIZE:
            logger.info(f"[TED] Last page reached at page {page}.")
            break

    logger.info(f"[TED] Total raw notices fetched: {len(all_notices)}")
    return all_notices