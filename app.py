import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import openai
import os

st.title("שיחה עם GPT על ציוד שהוקלט")

# הגדרת ClientSettings
client_settings = ClientSettings(
    media_stream_constraints={"video": False, "audio": True},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# כפתור הקלטה
st.header("🎤 לחץ כדי להתחיל להקליט")
ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDRECV,
    client_settings=client_settings
)

st.info("תכונת הקלטה חיה פועלת, אך עיבוד קובץ אודיו לא פעיל בגרסה זו.")

# למידע: אם תרצה לנתח את הקול – תצטרך ללכוד את הזרם בצד השרת, או לאפשר העלאת קובץ (mp3/wav) כמו שעשית בעבר.
