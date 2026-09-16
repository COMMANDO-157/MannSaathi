from transformers import pipeline
from backend.models.schemas import JournalEntry, EmotionalReading
import statistics

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
    return _classifier

def score_entry(entry: JournalEntry) -> tuple[float, float]:
    clf = get_classifier()
    result = clf(entry.text)[0]
    # TODO: map emotion label -> (valence, arousal) properly
    valence = 0.0
    arousal = 0.0
    return valence, arousal

def compute_baseline_deviation(user_id: str, valence: float, history: list[float]) -> float:
    if len(history) < 3:
        return 0.0
    mean = statistics.mean(history)
    stdev = statistics.stdev(history) or 1e-6
    return abs(valence - mean) / stdev

def analyze(entry: JournalEntry, user_history: list[float]) -> EmotionalReading:
    valence, arousal = score_entry(entry)
    deviation = compute_baseline_deviation(entry.user_id, valence, user_history)
    return EmotionalReading(
        user_id=entry.user_id,
        entry_id=str(entry.timestamp),
        valence_score=valence,
        arousal_score=arousal,
        baseline_deviation=deviation,
    )