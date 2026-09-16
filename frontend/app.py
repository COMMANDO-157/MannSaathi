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
        "user_history": [],
    })
    if resp.ok:
        data = resp.json()
        st.subheader(f"Tier: {data['tier']['tier'].upper()}")
        st.write(data["response"])
    else:
        st.error("Backend error")
    