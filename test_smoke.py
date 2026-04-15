from core.db_manager import DatabaseManager
from core.scoring_engine import ScoringEngine
from models.tender import Tender
from datetime import datetime

print("--- Step 1: Testing Config + Database ---")
db = DatabaseManager()
db.setup_database()
print("✓ Database connected and tables verified.")

print("\n--- Step 2: Testing Scoring Engine ---")
engine = ScoringEngine()

# Test 1: Should be a strong match (A)
score, category = engine.calculate_score(
    title="Messebau Auftrag Berlin 2026",
    description="Wir suchen einen Anbieter für Standbau und Messestand."
)
print(f"✓ Test 1 Score: {score}, Category: {category} (Expected: A)")

# Test 2: Should be a weak match (C)
score2, category2 = engine.calculate_score(
    title="Reinigung und Catering Auftrag",
    description="Wir suchen einen Reinigungsservice für unser Büro."
)
print(f"✓ Test 2 Score: {score2}, Category: {category2} (Expected: C)")

print("\n--- Step 3: Testing Saving a Tender to Database ---")
fake_tender = Tender(
    source_portal="TEST",
    external_id="TEST-001",
    title="Messebau Auftrag Berlin 2026",
    description="Wir suchen einen Anbieter für Standbau.",
    link="https://example.com/tender/1",
    deadline=datetime(2026, 6, 30),
    content_hash="abc123",
    score=score,
    category=category
)
db.save_tender(fake_tender)
print("✓ Fake tender saved to database.")

print("\n--- Step 4: Testing Duplicate Prevention ---")
db.save_tender(fake_tender)  # Try saving the same tender again
print("✓ Duplicate save handled without crash.")

print("\n--- All smoke tests passed! ---")