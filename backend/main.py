from fastapi import FastAPI
from pydantic import BaseModel
from backend.graph import build_graph

app = FastAPI(title="MannSaathi")
pipeline = build_graph()

# In-memory baseline history store: {user_id: [valence_score, ...]}
# TODO: replace with persistent DB before production
_user_history_store: dict[str, list[float]] = {}

class JournalRequest(BaseModel):
    user_id: str
    text: str

@app.post("/journal")
def process_journal(req: JournalRequest):
    history = _user_history_store.get(req.user_id, [])

    result = pipeline.invoke({
        "user_id": req.user_id,
        "raw_text": req.text,
        "audio_path": None,
        "user_history": history,
    })

    # store this entry's valence for future baseline comparisons
    new_valence = result["reading"]["valence_score"]
    _user_history_store.setdefault(req.user_id, []).append(new_valence)

    return {
        "response": result["final_response"],
        "tier": result["tier"],
        "reading": result["reading"],
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/history/{user_id}")
def get_history(user_id: str):
    return {"user_id": user_id, "history": _user_history_store.get(user_id, [])}