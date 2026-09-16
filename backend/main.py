from fastapi import FastAPI
from pydantic import BaseModel
from backend.graph import build_graph

app = FastAPI(title="MannSaathi")
pipeline = build_graph()

class JournalRequest(BaseModel):
    user_id: str
    text: str
    user_history: list[float] = []

@app.post("/journal")
def process_journal(req: JournalRequest):
    result = pipeline.invoke({
        "user_id": req.user_id,
        "raw_text": req.text,
        "audio_path": None,
        "user_history": req.user_history,
    })
    return {"response": result["final_response"], "tier": result["tier"]}

@app.get("/health")
def health():
    return {"status": "ok"}