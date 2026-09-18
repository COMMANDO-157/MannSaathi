"""
Evaluates the emotion classifier against a real labeled benchmark (dair-ai/emotion),
and compares it against a naive keyword-based baseline.
Run with: python -m backend.evaluate
"""
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score, classification_report
from backend.agents.analysis_agent import score_entry
from backend.models.schemas import JournalEntry

# dair-ai/emotion labels: 0=sadness, 1=joy, 2=love, 3=anger, 4=fear, 5=surprise
POSITIVE_LABELS = {1, 2, 5}
NEGATIVE_LABELS = {0, 3, 4}

NEGATIVE_KEYWORDS = {"sad", "bad", "hate", "angry", "cry", "afraid", "scared", "hurt", "depressed", "anxious", "alone", "tired", "hopeless"}
POSITIVE_KEYWORDS = {"happy", "good", "great", "love", "joy", "excited", "wonderful", "amazing", "glad", "fun"}


def run_eval(sample_size=150):
    print("Loading dair-ai/emotion test split...")
    dataset = load_dataset("dair-ai/emotion", split="test").select(range(sample_size))

    y_true, y_pred = [], []
    for row in dataset:
        text, label = row["text"], row["label"]
        true_sentiment = "positive" if label in POSITIVE_LABELS else "negative"

        entry = JournalEntry(user_id="eval", text=text, source="text")
        valence, _ = score_entry(entry)
        pred_sentiment = "positive" if valence >= 0 else "negative"

        y_true.append(true_sentiment)
        y_pred.append(pred_sentiment)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label="positive")

    print(f"\n--- Evaluation on {sample_size} real labeled examples (dair-ai/emotion) ---")
    print(f"Accuracy: {acc:.3f}")
    print(f"F1 Score: {f1:.3f}")
    print("\n" + classification_report(y_true, y_pred))

    return {"accuracy": acc, "f1": f1, "sample_size": sample_size}


def naive_keyword_predict(text: str) -> str:
    words = set(text.lower().split())
    neg_hits = len(words & NEGATIVE_KEYWORDS)
    pos_hits = len(words & POSITIVE_KEYWORDS)
    if neg_hits == 0 and pos_hits == 0:
        return "positive"
    return "positive" if pos_hits >= neg_hits else "negative"


def run_comparison(sample_size=150):
    dataset = load_dataset("dair-ai/emotion", split="test").select(range(sample_size))

    y_true, y_pred_model, y_pred_naive = [], [], []
    for row in dataset:
        text, label = row["text"], row["label"]
        true_sentiment = "positive" if label in POSITIVE_LABELS else "negative"

        entry = JournalEntry(user_id="eval", text=text, source="text")
        valence, _ = score_entry(entry)
        pred_model = "positive" if valence >= 0 else "negative"
        pred_naive = naive_keyword_predict(text)

        y_true.append(true_sentiment)
        y_pred_model.append(pred_model)
        y_pred_naive.append(pred_naive)

    model_acc = accuracy_score(y_true, y_pred_model)
    model_f1 = f1_score(y_true, y_pred_model, pos_label="positive")
    naive_acc = accuracy_score(y_true, y_pred_naive)
    naive_f1 = f1_score(y_true, y_pred_naive, pos_label="positive")

    print(f"\n--- Trained Model vs. Naive Keyword Baseline ({sample_size} real examples) ---")
    print(f"Trained Model  -> Accuracy: {model_acc:.3f} | F1: {model_f1:.3f}")
    print(f"Naive Keyword  -> Accuracy: {naive_acc:.3f} | F1: {naive_f1:.3f}")
    print(f"\nImprovement: +{(model_acc - naive_acc)*100:.1f}% accuracy, +{(model_f1 - naive_f1)*100:.1f}% F1")

    return {"model": {"acc": model_acc, "f1": model_f1}, "naive": {"acc": naive_acc, "f1": naive_f1}}


if __name__ == "__main__":
    run_eval()
    run_comparison()