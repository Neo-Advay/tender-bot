import re
from core.config_loader import load_config

class ScoringEngine:
    def __init__(self):
        self.config = load_config()
        self.strong_keywords = self.config['relevance']['keywords_strong']
        self.secondary_keywords = self.config['relevance']['keywords_secondary']
        
    def calculate_score(self, title, description):
        text = f"{title} {description}".lower()
        score = 0
        
        # Check strong keywords (e.g., Messebau) - higher weight
        for kw in self.strong_keywords:
            if re.search(rf"\b{kw.lower()}\b", text):
                score += 30  # Give 30 points per strong keyword
                
        # Check secondary keywords (e.g., Montage) - lower weight
        for kw in self.secondary_keywords:
            if re.search(rf"\b{kw.lower()}\b", text):
                score += 10  # Give 10 points per secondary keyword
        
        # Normalize score to max 100
        final_score = min(score, 100)
        
        # Assign Category
        if final_score >= 60:
            category = 'A'
        elif final_score >= 30:
            category = 'B'
        else:
            category = 'C'
            
        return final_score, category

# Usage test
# engine = ScoringEngine()
# score, cat = engine.calculate_score("Messebau in Berlin", "Wir suchen Standbau-Profis.")