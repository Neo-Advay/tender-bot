# test_runner.py

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))  # Ensures root is in path

# ── Phase 1a: Test Client ──────────────────────────────────────────────────────
def test_client():
    from connectors.ted import client
    data = client.fetch_raw_notices()
    print(f"✅ Fetched {len(data)} notices")
    if not data:
        print("No data returned. Stop here and fix the client.py first")
        return []
    
    print("Sample keys:", list(data[0].keys()))
    print("Sample item:", data[0])
    
    return data

# ── Phase 1b: Test Mapper ──────────────────────────────────────────────────────
def test_mapper(raw):
    from connectors.ted import mapper
    mapped = mapper.map_collection(raw)
    print(f"✅ Mapped {len(mapped)} notices")
    print(f"   Sample keys: {list(mapped[0].keys())}")
    return mapped

# ── Phase 1c: Test Normalization ───────────────────────────────────────────────
def test_normalization(mapped):
    from core.normalization import normalize_collection
    normalized = normalize_collection(mapped)
    print(f"✅ Normalized {len(normalized)} tenders")
    t = normalized[0]
    print(f"   Title: {t.title}")
    print(f"   Date: {t.publication_date}")
    print(f"   Hash: {t.content_hash}")
    return normalized

# ── Phase 1d: Test Scoring ─────────────────────────────────────────────────────
def test_scoring(normalized):
    from core.scoring_engine import ScoringEngine
    engine = ScoringEngine()
    scored = engine.score_collection(normalized)
    print(f"✅ Scored {len(scored)} tenders")
    print(f"   Sample score: {scored[0].score} ({scored[0].score_category})")
    return scored

# ── Phase 1e: Test DB ──────────────────────────────────────────────────────────
def test_db(scored):
    from core.db_manager import DatabaseManager
    db = DatabaseManager()
    t = scored[0]

    # Insert
    db.insert_tender(t)
    print(f"✅ Inserted tender: {t.external_id}")

    # Fetch back
    fetched = db.get_by_external_id(t.source, t.external_id)
    print(f"✅ Fetched back: {fetched.title}")

    # Update
    t.title = t.title + " [UPDATED]"
    db.update_tender(t)
    fetched2 = db.get_by_external_id(t.source, t.external_id)
    print(f"✅ Updated title: {fetched2.title}")

    return db, scored

# ── Phase 2: Test Ingest ───────────────────────────────────────────────────────
def test_ingest(scored, db):
    from pipeline.ingest import ingest_tenders
    summary, to_notify = ingest_tenders(scored, db, source="TED_EU")
    print(f"✅ Ingest summary: {summary}")
    print(f"   Tenders to notify: {len(to_notify)}")

# ── Run what you need ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    raw        = test_client()
    if not raw:
        raise SystemExit("Stopping because client returned no data")
    # mapped     = test_mapper(raw)
    # normalized = test_normalization(mapped)
    # scored     = test_scoring(normalized)
    # db, scored = test_db(scored)
    # test_ingest(scored, db)