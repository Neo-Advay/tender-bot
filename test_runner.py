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
    from core.config_loader import load_config

    # # Print what keywords the engine loaded
    # config = load_config()
    # relevance = config.get('relevance', {})
    # print("   Strong keywords:", relevance.get('strong_keywords', []))
    # print("   Secondary keywords:", relevance.get('secondary_keywords', []))

    engine = ScoringEngine()
    print("Strong keywords:", engine.strong_keywords)
    print("Secondary keywords:", engine.secondary_keywords)
    # Print what the first tender's title+description looks like
    t0 = normalized[0]
    print(f"   Title to match: '{t0.title}'")
    print(f"   Description:    '{t0.description[:100]}'")
    engine = ScoringEngine()
    scored = engine.score_collection(normalized)
    print(f"✅ Scored {len(scored)} tenders")

    # Show score distribution
    a = [t for t in scored if t.score_category == "A"]
    b = [t for t in scored if t.score_category == "B"]
    c = [t for t in scored if t.score_category == "C"]
    print(f"   Category A: {len(a)} | B: {len(b)} | C: {len(c)}")
    
    # Show top 3
    top = sorted(scored, key=lambda t: t.score, reverse=True)[:3]
    for t in top:
        print(f"   [{t.score_category}] {t.score:5.1f} | {t.title[:60]}")
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
    from datetime import datetime, timezone

    started_at = datetime.now(timezone.utc)
    summary, to_notify = ingest_tenders(scored, db, source="TED_EU")
    print(f"✅ Ingest complete")
    print(f"   New:       {summary['new']}")
    print(f"   Updated:   {summary['updated']}")
    print(f"   Unchanged: {summary['unchanged']}")
    print(f"   Errors:    {summary['errors']}")
    print(f"   To notify: {len(to_notify)}")

    if to_notify:
        print(f"   Sample notify: {to_notify[0].title[:60]}")

    return summary, to_notify
    # print(f"✅ Ingest summary: {summary}")
    # print(f"   Tenders to notify: {len(to_notify)}")

def test_mapper(raw):
    from connectors.ted import mapper
    mapped = mapper.map_collection(raw)
    print(f"✅ Mapped {len(mapped)} notices")
    t = mapped[0]
    print(f"   external_id:  {t['external_id']}")
    print(f"   title:        {t['title']}")
    print(f"   buyer_name:   {t['buyer_name']}")
    print(f"   buyer_country:{t['buyer_country']}")
    print(f"   notice_type:  {t['notice_type']}")
    print(f"   url:          {t['url']}")
    print(f"   pub_date:     {t['publication_date']}")
    return mapped

# ── Run what you need ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    raw        = test_client()
    if not raw:
        raise SystemExit("Stopping because client returned no data")
    mapped     = test_mapper(raw)
    normalized = test_normalization(mapped)
    scored     = test_scoring(normalized)
    db, scored = test_db(scored)
    summary, to_notify = test_ingest(scored, db)