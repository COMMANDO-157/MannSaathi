from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from backend.graph import build_graph
from backend.agents import interaction_agent
import tempfile, os

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

    new_valence = result["reading"]["valence_score"]
    _user_history_store.setdefault(req.user_id, []).append(new_valence)

    return {
        "response": result["final_response"],
        "tier": result["tier"],
        "reading": result["reading"],
    }

@app.post("/journal/voice")
async def process_voice_journal(user_id: str, audio: UploadFile = File(...)):
    suffix = os.path.splitext(audio.filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        entry = interaction_agent.build_journal_entry(user_id, audio_path=tmp_path)
    finally:
        os.remove(tmp_path)

    history = _user_history_store.get(user_id, [])
    result = pipeline.invoke({
        "user_id": user_id,
        "raw_text": entry.text,
        "audio_path": None,
        "user_history": history,
    })

    new_valence = result["reading"]["valence_score"]
    _user_history_store.setdefault(user_id, []).append(new_valence)

    return {
        "transcribed_text": entry.text,
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