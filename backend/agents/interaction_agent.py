from faster_whisper import WhisperModel
from backend.models.schemas import JournalEntry

_model: WhisperModel | None = None

def get_whisper_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model

def transcribe_audio(audio_path: str) -> str:
    model = get_whisper_model()
    segments, _ = model.transcribe(audio_path)
    return " ".join(seg.text for seg in segments)

def build_journal_entry(user_id: str, text: str = None, audio_path: str = None) -> JournalEntry:
    if audio_path:
        text = transcribe_audio(audio_path)
        source = "voice"
    else:
        source = "text"
    return JournalEntry(user_id=user_id, text=text, source=source)

def next_checkin_question(previous_responses: list[str]) -> str:
    # TODO: adaptive follow-up logic based on response history
    if not previous_responses:
        return "How has today felt compared to your usual days?"
    return "Can you say a bit more about what triggered that feeling?"