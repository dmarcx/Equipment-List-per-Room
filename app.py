import streamlit as st
import pandas as pd
import os
from openai import OpenAI, RateLimitError
import openai
import tempfile
import base64
import requests
import re

# הגדרת סיסמה
PASSWORD = "1234"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        with st.form("Password Form"):
            password = st.text_input("הזן סיסמה לגישה", type="password")
            submitted = st.form_submit_button("אשר")
            if submitted:
                if password == PASSWORD:
                    st.session_state.password_correct = True
                else:
                    st.error("סיסמה שגויה")
        return False
    else:
        return True

if not check_password():
    st.stop()

# הגדרת נתיב לתיקיית הקבצים
DATA_FOLDER = "."

st.set_page_config(page_title="שליפת ציוד לפי חדר", layout="wide")

# עיצוב כללי ודחיפת CSS עם תמיכה ב-RTL
st.markdown("""
    <style>
        body, .main, .block-container {
            direction: rtl;
            text-align: right;
        }
        .main h1 {text-align: center; color: #2c3e50;}
        .block-container {padding-top: 2rem;}
        .stDataFrame {background-color: #f9f9f9; border-radius: 8px; padding: 1rem;}
        .sidebar-logo {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# לוגו בתוך ה-sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image("SLD LOGO.png", width=160)
    st.markdown('</div>', unsafe_allow_html=True)
    st.header("\U0001F3E2 ניווט")

    # שלב 1: בחירת קומה
    floor_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    floor_codes = sorted([f.replace(".csv", "") for f in floor_files])
    selected_floor = st.selectbox("בחר קומה:", floor_codes)

# שלב 2: טעינת נתוני הקומה שנבחרה
floor_path = os.path.join(DATA_FOLDER, f"{selected_floor}.csv")
df = pd.read_csv(floor_path)
df.columns = df.columns.str.strip()
df['מספר חדר'] = df['מספר חדר'].astype(str).apply(lambda x: re.sub(r'[^֐-׿a-zA-Z0-9\s\-]', '', x.strip()))

# בדיקה של הערכים הייחודיים
st.write("הערכים הייחודיים בעמודת 'מספר חדר':", df['מספר חדר'].unique())

# שלב 3: טעינת מפרט תאורה אם הועלה או ברירת מחדל
spec_df = pd.DataFrame()
default_spec_path = os.path.join(DATA_FOLDER, "מפרט תאורה - L0001.xlsx")
uploaded_spec_file = st.file_uploader("העלה קובץ מפרט תאורה (Excel)", type=["xlsx"])

if uploaded_spec_file:
    spec_df = pd.read_excel(uploaded_spec_file)
    st.info("\U0001F4C2 נטען קובץ מפרט שהועלה על־ידך.")
elif os.path.exists(default_spec_path):
    spec_df = pd.read_excel(default_spec_path)
    st.info("\U0001F4C1 נטען קובץ ברירת מחדל מהמיקום הקבוע.")
else:
    st.warning("⚠️ לא נטען קובץ מפרט. אנא העלה קובץ ידנית.")

spec_df.columns = spec_df.columns.str.strip()
if not spec_df.empty:
    st.markdown("### \U0001F9FE מפרט תאורה:")
    st.dataframe(spec_df, use_container_width=True)
    st.write("\U0001F50D שמות עמודות במפרט:", list(spec_df.columns))

# שלב 4: הצגת רשימת חדרים בטבלה
room_numbers = sorted(df['מספר חדר'].unique())
st.markdown(f"### \U0001F4CD חדרים זמינים בקומה {selected_floor}:")

# הצגה בטבלה של 10 חדרים בכל שורה
for i in range(0, len(room_numbers), 10):
    row = "\t".join(str(room) for room in room_numbers[i:i+10])
    st.code(row, language='')

# Sidebar המשך בחירה
with st.sidebar:
    all_rooms_option = "הצג את כל הקומה"
    selected_rooms = st.multiselect("בחר חדרים להצגת הציוד:", options=room_numbers, default=[])

    if not selected_rooms:
        room_data = df.copy()
    else:
        room_data = df[df['מספר חדר'].isin(selected_rooms)]

    categories = ['הצג הכל'] + sorted(room_data['קטגוריה'].dropna().unique())
    types = ['הצג הכל'] + sorted(room_data['סוג'].dropna().unique())

    selected_category = st.selectbox("סנן לפי קטגוריה:", categories)
    selected_type = st.selectbox("סנן לפי סוג:", types)

# סינון בפלט הראשי
filtered_data = room_data.copy()
if selected_category != 'הצג הכל':
    filtered_data = filtered_data[filtered_data['קטגוריה'] == selected_category]
if selected_type != 'הצג הכל':
    filtered_data = filtered_data[filtered_data['סוג'] == selected_type]

# שיחה עם GPT
st.markdown("---")
st.markdown("### 🤖 שאל את GPT על הציוד שבחרת:")

user_question = st.text_input("מה תרצה לדעת?")

def ask_gpt(prompt, context_df, spec_df=None):
    context = context_df.to_string(index=False)

    spec_context = ""
    if spec_df is not None and not spec_df.empty:
        relevant_rooms = context_df['מספר חדר'].unique()
        filtered_spec = spec_df[spec_df['מספר חדר'].isin(relevant_rooms)]
        if not filtered_spec.empty:
            spec_lines = []
            for _, row in filtered_spec.iterrows():
                spec_lines.append(
                    f"חדר {row['מספר חדר']}: נדרש {row['מספר יחידות']} יחידות של גוף {row['סוג גוף תאורה']} "
                    f"בעוצמה של {row['עוצמה נדרשת (LUX)']} לוקס, מיקום: {row['מיקום']}."
                )
            spec_context = "\n\nמפרט דרישות התאורה:\n" + "\n".join(spec_lines)

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "אתה עוזר חכם בתחום ניתוח נתונים טכניים של ציוד לפי חדרים."},
                {"role": "user", "content": f"""הנתונים:
{context}
{spec_context}

שאלה:
{prompt}"""}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        return "⚠ OpenAI קיבל יותר מדי בקשות בזמן קצר. נסה שוב בעוד מספר דקות."

if user_question:
    gpt_answer = ask_gpt(user_question, filtered_data, spec_df)
    st.markdown(f"**תשובת GPT:**\n\n{gpt_answer}")
