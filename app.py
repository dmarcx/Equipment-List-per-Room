import streamlit as st
import openai
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import queue
import time
import os

openai.api_key = st.secrets["OPENAI_API_KEY"]

model = whisper.load_model("base")
q = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q.put(indata.copy())

def record_audio(duration=5, samplerate=16000):
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=samplerate):
        st.info("🎤 דבר בבקשה...")
        audio_data = np.empty((0, 1), dtype=np.float32)
        start_time = time.time()
        while time.time() - start_time < duration:
            audio_data = np.append(audio_data, q.get(), axis=0)
        return audio_data.flatten(), samplerate

def transcribe_audio(audio_np, samplerate):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio_np, samplerate)
        result = model.transcribe(f.name, language="he")
        os.remove(f.name)
        return result["text"]

def ask_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# UI
st.title("🗣️ שיחה קולית חיה עם GPT")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.button("🎤 התחל הקלטה"):
    audio, sr = record_audio(duration=6)
    user_text = transcribe_audio(audio, sr)
    gpt_reply = ask_gpt(user_text)

    st.session_state.chat_history.append(("👤", user_text))
    st.session_state.chat_history.append(("🤖", gpt_reply))

# הצגת שיחה
for speaker, msg in st.session_state.chat_history:
    st.markdown(f"**{speaker}**: {msg}")
