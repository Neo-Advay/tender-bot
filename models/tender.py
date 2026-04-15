from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Tender(Base):
    __tablename__ = 'tenders'

    id = Column(Integer, primary_key=True)
    source_portal = Column(String(50))   # e.g., 'TED', 'VergabeNRW'
    external_id = Column(String(100), unique=True) # ID from the website
    title = Column(String(500))
    description = Column(Text)
    link = Column(String(1000))
    deadline = Column(DateTime, nullable=True)
    
    # Discovery metadata
    found_at = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String(64))    # To detect updates
    
    # Scoring
    score = Column(Float, default=0.0)
    category = Column(String(1))         # A, B, or C