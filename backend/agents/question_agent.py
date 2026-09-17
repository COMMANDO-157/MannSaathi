import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client

def generate_next_question(previous_answer: str, valence: float, conversation_so_far: list[str]) -> str:
    """Generates one short, natural follow-up question based on the user's last answer."""
    tone_hint = "gentle and deeper" if valence < -0.1 else "warm and light"
    context = " ".join(conversation_so_far[-3:])  # last 3 exchanges for context, keep prompt short

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # fast, cheap, sufficient for short question generation
            messages=[
                {"role": "system", "content": (
                    "You are a warm, emotionally intelligent check-in companion. "
                    f"Ask ONE short, natural follow-up question in a {tone_hint} tone, based on what the user just said. "
                    "Keep it under 15 words. No preamble, just the question."
                )},
                {"role": "user", "content": f"Recent context: {context}\nTheir last answer: {previous_answer}"},
            ],
            max_tokens=40,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback to pool-based question if API fails/times out — keeps app functional offline
        from data.checkin_questions import QUESTIONS
        import random
        pool = "probe_deep" if valence < -0.1 else "probe_light"
        return random.choice(QUESTIONS[pool])