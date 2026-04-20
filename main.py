# main.py

import logging
import sys
from core.config_loader import load_config
from pipeline.run_pipeline import run_connector
from connectors.ted import client as ted_client
from connectors.ted import mapper as ted_mapper

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ── Logging setup ──────────────────────────────────────────────────────────────
config = load_config()

logging.basicConfig(
    level=getattr(logging, config.get('log_level', 'INFO').upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),                  # Console
        logging.FileHandler("logs/tender_bot.log"),         # File
    ]
)

logger = logging.getLogger(__name__)

# ── Connector registry ─────────────────────────────────────────────────────────
# Add new connectors here as we build them
CONNECTORS = [
    {
        "name": "TED_EU",
        "client": ted_client,
        "mapper": ted_mapper,
        "enabled": True,
    },
    # Future connectors:
    # {"name": "DTVP",        "client": dtvp_client,   "mapper": dtvp_mapper,   "enabled": False},
    # {"name": "VergabeNRW",  "client": nrw_client,    "mapper": nrw_mapper,    "enabled": False},
]


# ── Main run ───────────────────────────────────────────────────────────────────
def run_all():
    """Runs all enabled connectors sequentially."""
    logger.info("=" * 60)
    logger.info("Tender Bot — Starting full run")
    logger.info("=" * 60)

    overall = {"new": 0, "updated": 0, "unchanged": 0, "errors": 0}

    for connector in CONNECTORS:
        if not connector.get("enabled", False):
            logger.info(f"[Main] Skipping disabled connector: {connector['name']}")
            continue

        logger.info(f"[Main] Running connector: {connector['name']}")
        summary = run_connector(
            connector_name=connector["name"],
            client=connector["client"],
            mapper=connector["mapper"],
        )

        # Aggregate totals
        for key in ["new", "updated", "unchanged", "errors"]:
            overall[key] += summary.get(key, 0)

    logger.info("=" * 60)
    logger.info(
        f"[Main] All connectors done — "
        f"New: {overall['new']}, Updated: {overall['updated']}, "
        f"Unchanged: {overall['unchanged']}, Errors: {overall['errors']}"
    )
    logger.info("=" * 60)

    return overall


if __name__ == "__main__":
    run_all()