import streamlit as st
import requests

st.set_page_config(page_title="MannSaathi", layout="wide")
st.title("MannSaathi — Emotional Wellbeing Companion")

st.markdown("This is an assistive companion, not a diagnostic tool.")

user_id = st.text_input("User ID", value="demo_user")
entry_text = st.text_area("How are you feeling today?")

if st.button("Submit journal entry"):
    resp = requests.post("http://localhost:8000/journal", json={
        "user_id": user_id,
        "text": entry_text,
    })
    if resp.ok:
        data = resp.json()
        reading = data["reading"]

        st.subheader(f"Tier: {data['tier']['tier'].upper()}")
        st.write(data["response"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Valence", f"{reading['valence_score']:.3f}")
        col2.metric("Arousal", f"{reading['arousal_score']:.3f}")
        col3.metric("Baseline Deviation", f"{reading['baseline_deviation']:.3f}")
    else:
        st.error("Backend error")

st.divider()
if st.button("Show my entry history"):
    hist = requests.get(f"http://localhost:8000/history/{user_id}")
    if hist.ok:
        history = hist.json()["history"]
        if history:
            st.line_chart(history)
            st.caption(f"{len(history)} entries recorded for {user_id}")
        else:
            st.info("No entries yet.")