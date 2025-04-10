import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import whisper
import openai
import numpy as np
import av
import os
import tempfile
import soundfile as sf

# הגדרות בסיס
st.set_page_config(page_title="🎙️ שיחה קולית עם GPT", layout="centered")
st.title("🎤 שיחה קולית עם GPT")
st.info("דבר אל המיקרופון – ההקלטה תישמר, תתומלל ותישלח ל־GPT.")

# מפתח API של OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# טעינת מודל Whisper
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# היסטוריית שיחה
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# עיבוד אודיו
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recorded_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.recorded_frames.append(audio)
        return frame

# הקלטה
ctx = webrtc_streamer(
    key="speech",
    mode="SENDRECV",
    client_settings=ClientSettings(media_stream_constraints={"audio": True, "video": False}),
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

# שליחה ל־GPT
if ctx.audio_processor and st.button("🔍 נתח ושלח ל־GPT"):
    with st.spinner("⏳ ממיר קול לטקסט..."):
        audio_data = np.concatenate(ctx.audio_processor.recorded_frames, axis=0).flatten()
        temp_file = tempfile.mktemp(suffix=".wav")
        sf.write(temp_file, audio_data, 16000)

        transcription = model.transcribe(temp_file)["text"]
        st.success(f"🗣️ אתה אמרת: {transcription}")
        st.session_state.chat_history.append(("👤", transcription))

    with st.spinner("🤖 GPT חושב..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "אתה עוזר חכם לבדיקת ציוד."},
                *[
                    {"role": "user" if role == "👤" else "assistant", "content": msg}
                    for role, msg in st.session_state.chat_history
                ]
            ]
        )
        reply = response.choices[0].message.content.strip()
        st.session_state.chat_history.append(("🤖", reply))
        st.markdown(f"**GPT:** {reply}")

# הצגת שיחה
st.divider()
st.markdown("### 🧾 שיחה עד כה:")
for role, msg in reversed(st.session_state.chat_history):
    st.markdown(f"**{role}**: {msg}")
