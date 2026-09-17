import streamlit as st
import tempfile, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.graph import build_graph
from backend.agents import interaction_agent
from data.checkin_questions import QUESTIONS
from backend.graph import analyze_checkin_answer
import random
from backend.agents.voice_agent import text_to_speech
from backend.agents.question_agent import generate_next_question
from backend.db import save_journal_entry, get_journal_entries, get_valence_history, save_checkin, get_checkin_streak

st.set_page_config(page_title="MannSaathi", layout="wide")
st.title("MannSaathi — Emotional Wellbeing Companion")
st.markdown("This is an assistive companion, not a diagnostic tool.")

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
    if transcribed:
        st.info(f"Transcribed: \"{transcribed}\"")
    if tier_name == "severe":
        st.error(f"Tier: {tier_name.upper()}")
        st.markdown(result["final_response"])
    else:
        st.subheader(f"Tier: {tier_name.upper()}")
        st.write(result["final_response"])
    col1, col2, col3 = st.columns(3)
    col1.metric("Valence", f"{reading['valence_score']:.3f}")
    col2.metric("Arousal", f"{reading['arousal_score']:.3f}")
    col3.metric("Baseline Deviation", f"{reading['baseline_deviation']:.3f}")

user_id = st.text_input("User ID", value="demo_user")

tab_journal, tab_checkin, tab_history = st.tabs(["📓 Journal", "💬 Emotional Check-In", "📈 History"])

with tab_journal:
    st.caption("Free-form writing — say whatever's on your mind, like a diary.")
    entry_text = st.text_area("How are you feeling today?", key="journal_text")
    if st.button("Submit journal entry"):
        result = run_pipeline(user_id, entry_text, "text")
        render_result(result)

    st.info("Would you like to do a quick emotional check-in too?")
    if st.button("Start check-in", key="nudge_checkin"):
            st.session_state.active_tab_hint = "checkin"
            st.rerun()

    st.divider()
    st.subheader("Or record a voice entry")
    audio_value = st.audio_input("Record your check-in")
    if audio_value is not None and st.button("Submit voice entry"):
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

        answer_text = st.text_area("Your answer (or record below)", key=f"checkin_answer_{len(state['answers'])}")

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

        if st.button("Next →", key="checkin_next"):
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