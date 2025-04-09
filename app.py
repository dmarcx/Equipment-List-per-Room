
import streamlit as st
import pandas as pd
from openai import OpenAI

# טען את קובצי הנתונים
schedule_df = pd.read_excel("לוז לביצוע בדיקה לעבודה עם בוט.xlsx")
lighting_df = pd.read_excel("מפרט תאורה - L0001.xlsx")

# הגדרת ממשק המשתמש
st.set_page_config(page_title="שיחה עם בוט ציוד", layout="wide")
st.title("🤖 שוחח עם בוט הבדיקות")

st.markdown("הבוט מכיר את נתוני הבדיקות בלו"ז ואת מפרט התאורה לחדר L0001.")

# שדה להזנת שאלה
user_input = st.text_input("מה תרצה לדעת?", placeholder="לדוגמה: מה עוצמת התאורה הנדרשת בחדר L0001?")

# אם יש קלט מהמשתמש
if user_input:
    # הכנת הקשר מתוך הקבצים
    context_schedule = schedule_df.to_string(index=False)
    context_lighting = lighting_df.to_string(index=False)

    context = f"""
    זהו הלו"ז:
    {context_schedule}

    זהו מפרט התאורה:
    {context_lighting}
    """

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    with st.spinner("הבוט חושב..."):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "אתה בוט מומחה שמייעץ בנושא בדיקות ציוד לפי לו"ז ומפרטים טכניים."},
                {"role": "user", "content": f"הנתונים הם:\n{context}\n\nשאלתי היא: {user_input}"}
            ],
            temperature=0.4
        )

        answer = response.choices[0].message.content.strip()
        st.markdown(f"**תשובת הבוט:**\n\n{answer}")
