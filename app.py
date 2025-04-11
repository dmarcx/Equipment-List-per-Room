import streamlit as st
import openai
import tempfile
import os

# הכנס את המפתח שלך בקובץ הסודות (נראה בשלב הבא)
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("🎤 תמלול אודיו עם Whisper API")

audio_file = st.file_uploader("העלה קובץ קול (mp3, wav וכו')", type=["mp3", "wav", "m4a"])

if audio_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_file.read())
        tmp_path = tmp.name

    st.audio(audio_file, format='audio/mp3')
    st.write("⏳ מתמלל עם Whisper API...")

    with open(tmp_path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)

    st.success("✔️ תמלול הושלם!")
    st.subheader("📄 תוצאה:")
    st.text(transcript["text"])

    os.remove(tmp_path)