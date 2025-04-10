
import streamlit as st
import tempfile
import whisper
import openai
import os
import sounddevice as sd
import numpy as np
import scipy.io.wavfile

st.set_page_config(page_title="🎙️ שיחה קולית עם GPT", layout="centered")

st.title("🎙️ על ציוד שהוקלט GPT שיחה עם")
st.markdown("## לחץ כדי להתחיל להקליט")

openai.api_key = os.environ.get("OPENAI_API_KEY")

def record_audio(duration=5, fs=44100):
    st.info("⏺️ מקליט עכשיו...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return fs, audio

def save_wav_file(fs, audio):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        scipy.io.wavfile.write(f.name, fs, audio)
        return f.name

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

def ask_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

if "conversation" not in st.session_state:
    st.session_state.conversation = []

if st.button("🎤 התחל הקלטה"):
    fs, audio = record_audio(duration=7)
    wav_file = save_wav_file(fs, audio)
    user_text = transcribe_audio(wav_file)
    st.session_state.conversation.append(("👤 אתה", user_text))
    gpt_reply = ask_gpt(user_text)
    st.session_state.conversation.append(("🤖 GPT", gpt_reply))

for speaker, text in reversed(st.session_state.conversation):
    st.markdown(f"**{speaker}:** {text}")
