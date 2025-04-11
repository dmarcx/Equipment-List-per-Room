import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import whisper
import av
import numpy as np
import tempfile
import os

# טען את מודל whisper פעם אחת
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# הגדרת עיבוד האודיו
class AudioProcessor:
    def __init__(self):
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.frames.append(audio)
        return frame

    def get_audio_data(self):
        if not self.frames:
            return None
        audio_data = np.concatenate(self.frames, axis=1)[0]
        return audio_data

    def reset(self):
        self.frames = []

# ממשק למשתמש
st.title("🎙️ דיבור חי ל-Text עם Whisper")

webrtc_ctx = webrtc_streamer(
    key="live-audio",
    mode=WebRtcMode.SENDONLY,
    in_audio=True,
    client_settings=ClientSettings(
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    ),
    audio_processor_factory=AudioProcessor,
)

if st.button("🔄 סיים וזיהוי טקסט"):
    if webrtc_ctx.audio_processor:
        audio_data = webrtc_ctx.audio_processor.get_audio_data()
        webrtc_ctx.audio_processor.reset()

        if audio_data is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                import soundfile as sf
                sf.write(f.name, audio_data, 48000)
                st.success("הקלטה נשמרה")

                result = model.transcribe(f.name, language='he')
                st.text_area("🎧 טקסט מזוהה", result["text"])
                os.unlink(f.name)
        else:
            st.warning("לא זוהתה הקלטה.")
