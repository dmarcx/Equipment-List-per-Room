
import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import whisper
import openai
import numpy as np
import av
import os
import tempfile

st.set_page_config(page_title="🎙️ שיחה קולית עם GPT", layout="centered")

# מפתח ה-API של OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")

# טעינת מודל Whisper
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

# הצגת כותרת
st.title("🎤 שיחה קולית עם GPT")
st.info("דבר אל המיקרופון – הקלטה תנותח ותישלח ל־GPT.")

# שמירת היסטוריית שיחה
if "chat_history" not in st.session_state:
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

# כפתור להפעלת הניתוח הקולי
if ctx.audio_processor and st.button("🔍 שלח ל-GPT"):
    with st.spinner("⏳ ממיר קול לטקסט..."):
        audio_data = np.concatenate(ctx.audio_processor.recorded_data, axis=0).flatten()
        temp_audio_path = tempfile.mktemp(suffix=".wav")
        import soundfile as sf
        sf.write(temp_audio_path, audio_data, 16000)

        transcription = model.transcribe(temp_audio_path)["text"]
        st.success(f"🗣️ אתה אמרת: {transcription}")

        # שמירה בהיסטוריה
        st.session_state.chat_history.append(("👤", transcription))

    with st.spinner("🤖 GPT חושב..."):
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

# הצגת היסטוריה
st.divider()
st.markdown("## 🧾 שיחה עד כה:")
for role, msg in reversed(st.session_state.chat_history):
    st.markdown(f"**{role}**: {msg}")
