import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import queue
import tempfile
import speech_recognition as sr
import soundfile as sf

# תור לאודיו
audio_queue = queue.Queue()

# פונקציית callback שמקבלת את האודיו מהדפדפן
def audio_callback(frame: av.AudioFrame) -> av.AudioFrame:
    audio_queue.put(frame.to_ndarray())
    return frame

# רכיב ההקלטה
ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=1024,
    client_settings=ClientSettings(
        media_stream_constraints={"audio": True, "video": False}
    ),
    audio_callback=audio_callback,
)

# בדיקה אם מתקבל אודיו
if ctx.state.playing:
    if not audio_queue.empty():
        st.success("המערכת מקבלת קול מהמיקרופון 🎤")
    else:
        st.warning("לא מתקבל קול – ודא שהמיקרופון פעיל.")

# כפתור לשליחה ל-GPT
if st.button("המר לטקסט ושלח ל-GPT"):
    if not audio_queue.empty():
        audio_data = b''.join([frame.tobytes() for frame in list(audio_queue.queue)])
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(temp_audio_file.name, audio_queue.get(), 16000)
        temp_audio_file.close()

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio_file.name) as source:
            audio = recognizer.record(source)
            try:
                query = recognizer.recognize_google(audio, language="he-IL")
                st.success(f"שאלה שתומללה: {query}")
                # כאן תכניס את הקריאה ל־GPT שלך:
                # gpt_answer = ask_gpt(query, filtered_data, spec_df)
                # st.markdown(f"**תשובת GPT:**\n\n{gpt_answer}")
            except sr.UnknownValueError:
                st.warning("לא ניתן היה להבין את הדיבור.")
            except sr.RequestError as e:
                st.error(f"שגיאה מהשרת: {e}")
    else:
        st.error("אין נתוני קול בתור. ודא שביצעת הקלטה.")
