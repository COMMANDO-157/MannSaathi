from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class JournalEntry(BaseModel):
    user_id: str
    text: str
    source: Literal["voice", "text"]
    timestamp: datetime = datetime.utcnow()

class EmotionalReading(BaseModel):
    user_id: str
    entry_id: str
    valence_score: float          # -1.0 (very negative) to 1.0 (very positive)
    arousal_score: float          # 0.0 (calm) to 1.0 (agitated)
    baseline_deviation: float     # std devs from personal baseline
    timestamp: datetime = datetime.utcnow()

class KnowledgeResult(BaseModel):
    query: str
    passages: list[str]
    sources: list[str]
    confidence: float

class EscalationTier(BaseModel):
    tier: Literal["mild", "moderate", "severe"]
    reasoning: str
    confidence: float
    recommended_action: str