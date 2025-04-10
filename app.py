import os
import tempfile

import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import numpy as np
import av
import whisper
import openai
import soundfile as sf

# הגדרות עמוד
st.set_page_config(page_title="🎙️ שיחה קולית עם GPT", layout="centered")

# בדיקת מפתח API
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("מפתח OpenAI API לא מוגדר. אנא הגדר את OPENAI_API_KEY.")
    st.stop()

# טעינת מודל Whisper – נטען רק כשצריך
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

# כותרת
st.title("🎤 שיחה קולית עם GPT")
st.info("דבר אל המיקרופון – הקלטה תנותח ותישלח ל־GPT.")

# היסטוריית שיחה
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# כפתור לאיפוס שיחה
if st.button("🔁 אפס שיחה"):
    st.session_state.chat_history = []

# עיבוד קול
class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.recorded_data = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.recorded_data.append(audio)
        return frame

# ממשק הקלטה
ctx = webrtc_streamer(
    key="speech-to-text",
    mode="SENDRECV",
    client_settings=ClientSettings(media_stream_constraints={"audio": True, "video": False}),
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

# לחצן לשליחת ההקלטה
if ctx.audio_processor and st.button("🔍 שלח ל-GPT"):
    with st.spinner("⏳ טוען את מודל Whisper..."):
        try:
            model = load_whisper_model()
        except Exception as e:
            st.error(f"שגיאה בטעינת מודל Whisper: {e}")
            st.stop()

    with st.spinner("⏳ ממיר קול לטקסט..."):
        try:
            audio_data = np.concatenate(ctx.audio_processor.recorded_data, axis=0).flatten()
            temp_audio_path = tempfile.mktemp(suffix=".wav")
            sf.write(temp_audio_path, audio_data, 16000)
            transcription = model.transcribe(temp_audio_path)["text"]
            st.success(f"🗣️ אתה אמרת: {transcription}")
            st.session_state.chat_history.append(("👤", transcription))
        except Exception as e:
            st.error(f"שגיאה בעיבוד הקול: {e}")
            st.stop()

    with st.spinner("🤖 GPT חושב..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "אתה עוזר חכם לבדיקת ציוד."},
                    *[
                        {"role": "user" if role == "👤" else "assistant", "content": msg}
                        for role, msg in st.session_state.chat_history
                    ],
                ]
            )
            gpt_reply = response.choices[0].message.content.strip()
            st.session_state.chat_history.append(("🤖", gpt_reply))
            st.markdown(f"**GPT:** {gpt_reply}")
        except Exception as e:
            st.error(f"שגיאה בקבלת תשובה מ־GPT: {e}")
            st.stop()

# הצגת היסטוריית שיחה
st.divider()
st.markdown("## 🧾 שיחה עד כה:")
for role, msg in reversed(st.session_state.chat_history):
    st.markdown(f"**{role}**: {msg}")
