from gtts import gTTS
import io

def text_to_speech(text: str) -> bytes:
    """Converts text to speech audio bytes (MP3) for Streamlit playback."""
    tts = gTTS(text=text, lang="en", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()