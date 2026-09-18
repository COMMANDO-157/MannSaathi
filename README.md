# MannSaathi

A Streamlit emotional wellbeing companion with text and voice journaling, guided
five-question check-ins, emotional trend charts, and downloadable summaries.

The interface uses a sage-and-cream theme, gentle animations, responsive spacing,
and reduced-motion support. This is an assistive demonstration, not a diagnostic
tool or a replacement for professional care.

## Run locally

Run from the repository root with Python 3.12 or newer:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run frontend/app.py
```

Optionally set `GROQ_API_KEY` in your environment or a local `.env` file to enable
AI-generated follow-up questions. Without it, the existing question-pool fallback
is used. Never commit credentials.

The Streamlit app imports the processing pipeline directly; a separate FastAPI
server is not needed to run or deploy this interface. Keep `data/knowledge.index`
and `data/knowledge_meta.pkl` in the repository for retrieval.

## Deploy on Streamlit Community Cloud

1. Sign in at <https://share.streamlit.io> and choose **Create app**.
2. Select repository `COMMANDO-157/MannSaathi`, branch `main`, and entrypoint
   `frontend/app.py`.
3. In **Advanced settings**, select Python **3.12**.
4. For generated follow-up questions, add the following to the private **Secrets**
   field, replacing the placeholder with your own key:

   ```toml
   GROQ_API_KEY = "your-groq-api-key"
   ```

5. Deploy and check the build logs. Verify journaling, a full five-question
   check-in, voice input, history, and summary download with fictional data.

Cloud deployment has not yet been verified. The first analysis, retrieval, and
voice transcription download model weights and may take longer. The app uses
PyTorch, an emotion classifier, a sentence embedder, and Whisper; verify memory
usage on the hosting tier. Text-to-speech requires network access.

See the official [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
and [secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Public demo limitations

- Use fictional entries only. There is no authentication: visitors with the same
  User ID can read the same saved journal history. The default ID is `demo_user`.
- SQLite stores entries on the app server, not just in the browser session.
  Cloud-local storage is not a durable backup and may be lost during redeployment.
- Check-in answers may be sent to Groq for follow-up generation. Spoken questions
  and summaries are sent to Google's text-to-speech service. Voice transcription
  uses Whisper on the app server.
- API keys, local journal databases, and virtual environments are excluded from Git.
- Private real-world use requires authentication, access controls, and appropriate
  persistent storage. Those backend changes are outside this UI update.

## Demo recording

Record with fictional data and a dedicated demo User ID:

1. Show the welcome page and enter the app.
2. Write a short journal entry and show its response.
3. Demonstrate a short voice entry.
4. Complete the guided check-in and show the summary.
5. Open History and download a session summary.

Add your recording link here once recorded and uploaded. No demo video is included yet.
