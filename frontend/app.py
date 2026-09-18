import streamlit as st
import tempfile, os, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.graph import build_graph
from backend.agents import interaction_agent
from data.checkin_questions import QUESTIONS
from backend.graph import analyze_checkin_answer
import random
from backend.agents.voice_agent import text_to_speech
from backend.agents.question_agent import generate_next_question
from backend.db import save_journal_entry, get_journal_entries, get_valence_history, save_checkin, get_checkin_streak

st.set_page_config(page_title="MannSaathi · A moment for you", page_icon="🌱", layout="wide")
st.html(Path(__file__).with_name("styles.css"))
st.html('''<div class="ms-brand"><div class="ms-mark" aria-hidden="true">✳</div>
MannSaathi <span>Your emotional wellbeing companion</span></div>''')


def render_hero(title, description):
    # Only static presentation copy is passed here, never journal content.
    st.html(f'''<section class="ms-hero"><div class="ms-orbit" aria-hidden="true"></div>
    <div class="ms-eyebrow">A little space. Just for you.</div>
    <h1>{title}</h1><p>{description}</p></section>''')


if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if not st.session_state.onboarded:
    render_hero("Every feeling deserves<br>a little room.",
                "Welcome to MannSaathi. A quiet place to reflect, check in with yourself, and take your day one moment at a time.")
    st.markdown("""
    **Before we begin, here's what this companion does — and doesn't do:**

    - Listens to your voice or text journal entries and understands how you're feeling
    - Notices when your emotional pattern shifts from your own recent baseline
    - Points you toward grounded, cited coping suggestions — or real human help when needed

    It does **not** diagnose any mental health condition.

    It is **not** a replacement for a therapist, doctor, or counselor.

    **Demo privacy:** Use fictional entries. Entries are stored on the server, and anyone
    using the same User ID can view that history. User IDs are not passwords.
    Guided check-in answers may be sent to Groq for follow-up questions, and spoken
    question/summary text is sent to Google's text-to-speech service.

    If at any point you're in crisis, this companion will always show you real, verified helplines.
    """)
    if st.button("I understand — let's begin", type="primary"):
        st.session_state.onboarded = True
        st.rerun()
    st.stop()

render_hero("Come as you are.", "Write it out, talk it through, or simply check in. There's no perfect way to begin — just your own.")
st.caption("This is an assistive companion, not a diagnostic tool.")
st.info("Demo: use fictional entries only. History is shared by User ID; a User ID is not a private account.")

if "pipeline" not in st.session_state:
    st.session_state.pipeline = build_graph()
if "history_store" not in st.session_state:
    st.session_state.history_store = {}
if "journal_log" not in st.session_state:
    st.session_state.journal_log = {}
if "checkin_log" not in st.session_state:
    st.session_state.checkin_log = {}

def run_pipeline(user_id, text, source):
    history = get_valence_history(user_id)
    result = st.session_state.pipeline.invoke({
        "user_id": user_id, "raw_text": text, "audio_path": None, "user_history": history,
    })
    reading = result["reading"]
    save_journal_entry(user_id, text, source, result["tier"]["tier"], reading["valence_score"])
    return result

def render_result(result, transcribed=None):
    reading = result["reading"]
    tier_name = result["tier"]["tier"]
    confidence = result["tier"]["confidence"]
    if transcribed:
        st.info(f"Transcribed: \"{transcribed}\"")
    if tier_name == "severe":
        st.error(f"Tier: {tier_name.upper()} (confidence: {confidence:.0%})")
        st.markdown(result["final_response"])
    else:
        st.subheader(f"Tier: {tier_name.upper()} (confidence: {confidence:.0%})")
        st.write(result["final_response"])
    col1, col2, col3 = st.columns(3)
    col1.metric("Valence", f"{reading['valence_score']:.3f}")
    col2.metric("Arousal", f"{reading['arousal_score']:.3f}")
    col3.metric("Baseline Deviation", f"{reading['baseline_deviation']:.3f}")

user_id = st.text_input("User ID", value="demo_user")

tab_journal, tab_checkin, tab_history = st.tabs(["📓 Journal", "💬 Emotional Check-In", "📈 History"])

with tab_journal:
    st.subheader("A moment to put it into words")
    st.caption("Free-form writing — say whatever's on your mind, like a diary.")
    entry_text = st.text_area("How are you feeling today?", key="journal_text", height=190,
                              placeholder="Today, what's on my mind is…")
    if st.button("Submit journal entry", type="primary"):
        with st.spinner("Taking a moment with your words…"):
            result = run_pipeline(user_id, entry_text, "text")
        render_result(result)

    
    st.divider()
    st.subheader("Or record a voice entry")
    audio_value = st.audio_input("Record your check-in")
    if audio_value is not None and st.button("Submit voice entry", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_value.getvalue())
            tmp_path = tmp.name
        try:
            entry = interaction_agent.build_journal_entry(user_id, audio_path=tmp_path)
        finally:
            os.remove(tmp_path)
        result = run_pipeline(user_id, entry.text, "voice")
        render_result(result, transcribed=entry.text)

    st.divider()
    st.subheader("Past entries")
    log = get_journal_entries(user_id)
    if log:
        for e in reversed(log[-10:]):
            with st.expander(f"{e['time']} — {e['tier'].upper()} (valence {e['valence']:.2f})"):
                st.write(e["text"])
    else:
        st.info("No journal entries yet.")

with tab_checkin:
    st.subheader("Let's take this one question at a time")
    st.caption("A short guided conversation to understand how you're really feeling — your answers are analyzed quietly in the background.")

    if "checkin_state" not in st.session_state:
        st.session_state.checkin_state = {}
    if "checkin_streak" not in st.session_state:
        st.session_state.checkin_streak = {}

    state = st.session_state.checkin_state.setdefault(user_id, {"answers": [], "readings": [], "current_q": None, "done": False})

    MAX_QUESTIONS = 5

    streak = get_checkin_streak(user_id)            
    if streak > 0:
        st.markdown(f"🔥 **{streak}-day check-in streak** — keep it going!")

    if not state["done"]:
        if state["current_q"] is None:
            state["current_q"] = random.choice(QUESTIONS["opening"])

        progress = len(state["answers"]) / MAX_QUESTIONS
        st.progress(progress, text=f"Question {len(state['answers']) + 1} of {MAX_QUESTIONS}")

        st.write(f"**{state['current_q']}**")

        # App speaks the question aloud
        audio_bytes = text_to_speech(state["current_q"])
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        answer_text = st.text_area("Your answer (or record below)", key=f"checkin_answer_{len(state['answers'])}", height=150,
                                   placeholder="Take your time. Whatever comes to mind is a place to start.")

        voice_answer = st.audio_input("Or answer by voice", key=f"checkin_voice_{len(state['answers'])}")
        if voice_answer is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(voice_answer.getvalue())
                tmp_path = tmp.name
            try:
                transcribed = interaction_agent.build_journal_entry(user_id, audio_path=tmp_path)
                answer_text = transcribed.text
                st.info(f"Heard: \"{answer_text}\"")
            finally:
                os.remove(tmp_path)

        answer = answer_text

        if st.button("Next →", key="checkin_next", type="primary"):
            if answer and answer.strip():               
                history = get_valence_history(user_id)
                reading = analyze_checkin_answer(user_id, answer, history)
                state["answers"].append(answer)
                state["readings"].append(reading)

                if len(state["answers"]) >= MAX_QUESTIONS:
                    state["done"] = True
                    streak = save_checkin(user_id, sum(v["valence_score"] for v in state["readings"])/len(state["readings"]),
                                          sum(v["arousal_score"] for v in state["readings"])/len(state["readings"]))
                else:
                    st.toast("Thanks for sharing that 💭", icon="✨")
                    state["current_q"] = generate_next_question(
                        answer, reading["valence_score"], state["answers"]
                    )
                st.rerun()

    if state["done"] or len(state["answers"]) >= MAX_QUESTIONS:
        st.success("Check-in complete! 🎉")

        valences = [r["valence_score"] for r in state["readings"]]
        arousals = [r["arousal_score"] for r in state["readings"]]
        avg_valence = sum(valences) / len(valences)
        avg_arousal = sum(arousals) / len(arousals)

        if avg_valence <= -0.6:
            emoji, label = "😢", "Things feel really heavy right now"
        elif avg_valence <= -0.3:
            emoji, label = "😔", "Today's been a tough one"
        elif avg_valence <= 0.1:
            emoji, label = "😐", "A pretty neutral day"
        elif avg_valence <= 0.5:
            emoji, label = "🙂", "A fairly good day"
        else:
            emoji, label = "😊", "A genuinely good day"

        st.markdown(f"<h1 style='text-align:center; font-size:80px'>{emoji}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center'>{label}</h3>", unsafe_allow_html=True)
        summary_audio = text_to_speech(f"{label}. Thanks for checking in today.")
        st.audio(summary_audio, format="audio/mp3", autoplay=True)

        if avg_valence <= -0.6:
            st.error("Please consider reaching out to **Tele-MANAS: 14416** (free, confidential, 24/7). If you're in immediate danger, call **112**.")
        elif avg_valence <= -0.3:
            st.warning("Consider talking to someone you trust — you don't have to carry this alone.")

        col1, col2 = st.columns(2)
        col1.metric("Average Valence", f"{avg_valence:.3f}")
        col2.metric("Average Arousal", f"{avg_arousal:.3f}")

        st.subheader("How your emotional tone shifted through the check-in")
        st.line_chart(valences)

        if st.button("Start a new check-in"):
            st.session_state.checkin_state[user_id] = {"answers": [], "readings": [], "current_q": None, "done": False}
            st.rerun()

with tab_history:
    st.subheader("Your reflections, over time")
    st.caption("A place to look back at what you've shared and notice your own patterns.")
    st.subheader("Valence trend (from journal entries)")
    history = get_valence_history(user_id)
    if history:
        st.line_chart(history)
        st.caption(f"{len(history)} journal entries recorded for {user_id}")
    else:
        st.info("No entries yet.")

    clog = st.session_state.checkin_log.get(user_id, [])
    if clog:
        st.subheader("Mood trend (from check-ins)")
        st.line_chart([c["mood"] for c in clog])
        st.divider()

    st.subheader("Export session summary")
    entries = get_journal_entries(user_id, limit=50)
    if entries:
        summary_lines = [f"MannSaathi Session Summary — {user_id}", "=" * 40, ""]
        for e in reversed(entries):
            summary_lines.append(f"[{e['time']}] Tier: {e['tier'].upper()} (valence {e['valence']:.2f})")
            summary_lines.append(f"  \"{e['text']}\"")
            summary_lines.append("")
        summary_text = "\n".join(summary_lines)

        st.download_button(
            "📄 Download session summary (for a therapist or trusted person)",
            data=summary_text,
            file_name=f"mannsaathi_summary_{user_id}.txt",
            mime="text/plain",
        )
    else:
        st.info("No entries yet to export.")

st.html('<footer class="ms-footer">MannSaathi · A little reflection, at your own pace.</footer>')
