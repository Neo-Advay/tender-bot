# core/scoring_engine.py

import logging
from models.canonical_tender import CanonicalTender
from core.config_loader import load_config

logger = logging.getLogger(__name__)


class ScoringEngine:
    def __init__(self):
        config = load_config()
        relevance = config.get('relevance', {})

        self.strong_keywords = [kw.lower() for kw in relevance.get('keywords_strong', [])]
        self.secondary_keywords = [kw.lower() for kw in relevance.get('keywords_secondary', [])]
        self.cpv_codes = [str(c) for c in relevance.get('cpv_codes', [])]

        # weights = config.get('weights', {})
        # self.weight_keyword = weights.get('keyword_score', 0.7)
        # self.weight_cpv = weights.get('cpv_score', 0.3)

    # def _keyword_score(self, tender: CanonicalTender) -> float:
    #     """Score based on keyword hits in title + description."""
    #     text = f"{tender.title} {tender.description}".lower()
    #     strong_hits = sum(1 for kw in self.strong_keywords if kw in text)
    #     secondary_hits = sum(1 for kw in self.secondary_keywords if kw in text)

    #     # Strong hits worth 2x secondary
    #     raw = (strong_hits * 2) + (secondary_hits * 1)
    #     max_possible = (len(self.strong_keywords) * 2) + len(self.secondary_keywords)

    #     return round(raw / max_possible, 4) if max_possible > 0 else 0.0

    # def _cpv_score(self, tender: CanonicalTender) -> float:
    #     """Score based on CPV code overlap."""
    #     if not self.cpv_codes or not tender.cpv_codes:
    #         return 0.0
    #     tender_cpvs = [str(c) for c in tender.cpv_codes]
    #     hits = sum(1 for c in tender_cpvs if c in self.cpv_codes)
    #     return round(hits / len(self.cpv_codes), 4)

    # def score(self, tender: CanonicalTender) -> CanonicalTender:
    #     """Score a single tender and assign category. Returns the same tender mutated."""
    #     kw_score = self._keyword_score(tender)
    #     cpv_score = self._cpv_score(tender)

    #     combined = (kw_score * self.weight_keyword) + (cpv_score * self.weight_cpv)
    #     tender.score = round(combined * 100, 2)  # Scale to 0–100

    #     if tender.score >= 60:
    #         tender.score_category = "A"
    #     elif tender.score >= 30:
    #         tender.score_category = "B"
    #     else:
    #         tender.score_category = "C"

    #     logger.debug(f"[Scoring] {tender.external_id} → Score: {tender.score} ({tender.score_category})")
    #     return tender

    def score_collection(self, tenders: list[CanonicalTender]) -> list[CanonicalTender]:
        """Score a list of tenders."""
        return [self.score(t) for t in tenders]
    
    def score(self, tender: CanonicalTender) -> CanonicalTender:
        score = 0.0
        title = (tender.title or "").lower()
        desc = (tender.description or "").lower()
        full_text = f"{title} {desc}"

        # 1. Strong Keyword Scoring (Max 60 points)
        for kw in self.strong_keywords:
            if kw in title:
                score += 40  # Found in title
            elif kw in desc:
                score += 25  # Found in description

        # 2. Secondary Keyword Scoring (Max 20 points)
        for kw in self.secondary_keywords:
            if kw in title:
                score += 15
            elif kw in desc:
                score += 10

        # 3. CPV Scoring (Max 20 points)
        if tender.cpv_codes:
            for t_cpv in tender.cpv_codes:
                # Match if tender CPV starts with any of our config codes (prefix match)
                if any(str(t_cpv).startswith(str(c)) for c in self.cpv_codes):
                    score += 20
                    break

        # Final cap and category assignment
        tender.score = min(float(round(score, 2)), 100.0)

        if tender.score >= 70:
            tender.score_category = "A"
        elif tender.score >= 30:
            tender.score_category = "B"
        else:
            tender.score_category = "C"

        return tender