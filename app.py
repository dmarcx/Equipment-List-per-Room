import streamlit as st
import whisper
import tempfile
import os

# טוען את המודל ישירות בלי cache
def load_model():
    try:
        model = whisper.load_model("base")
        st.success("Whisper model loaded successfully.")
        return model
    except Exception as e:
        st.error(f"Failed to load Whisper model: {e}")
        return None

model = load_model()

# ממשק המשתמש
st.title("🎤 Speech to Text with Whisper")

# העלאת קובץ אודיו
audio_file = st.file_uploader("העלה קובץ קול (mp3, wav וכו')", type=["mp3", "wav", "m4a"])

if audio_file and model:
    # שומר זמנית את הקובץ
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_file.read())
        tmp_path = tmp.name

    st.audio(audio_file, format='audio/mp3')

    # התחלת תמלול
    st.write("⏳ מתמלל...")
    result = model.transcribe(tmp_path)
    st.success("✔️ תמלול הושלם!")

    st.subheader("📄 תוצאה:")
    st.text(result["text"])

    # מחיקת הקובץ הזמני
    os.remove(tmp_path)
