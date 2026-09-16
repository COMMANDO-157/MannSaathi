from transformers import pipeline
from backend.models.schemas import JournalEntry, EmotionalReading
import statistics

_classifier = None

# Circumplex model coordinates: (valence, arousal) per emotion label
# valence: -1 (negative) to 1 (positive) | arousal: 0 (calm) to 1 (agitated)
EMOTION_COORDINATES = {
    "anger":    (-0.6, 0.9),
    "disgust":  (-0.6, 0.5),
    "fear":     (-0.7, 0.8),
    "joy":      (0.8, 0.6),
    "neutral":  (0.0, 0.1),
    "sadness":  (-0.7, 0.3),
    "surprise": (0.2, 0.8),
}

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
        )
    return _classifier

def score_entry(entry: JournalEntry) -> tuple[float, float]:
    clf = get_classifier()
    results = clf(entry.text)[0]

    total_weight = sum(r["score"] for r in results)
    if total_weight == 0:
        return 0.0, 0.0

    valence = sum(EMOTION_COORDINATES[r["label"]][0] * r["score"] for r in results) / total_weight
    arousal = sum(EMOTION_COORDINATES[r["label"]][1] * r["score"] for r in results) / total_weight

    return round(valence, 4), round(arousal, 4)

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
