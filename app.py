import streamlit as st
import pandas as pd
import os
from openai import OpenAI, RateLimitError
import openai
import tempfile
import base64
import requests

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

# שלב 3: טעינת מפרט תאורה אם הועלה
uploaded_spec_file = st.file_uploader("העלה קובץ מפרט תאורה (Excel)", type=["xlsx"])
if uploaded_spec_file:
    spec_df = pd.read_excel(uploaded_spec_file)
    spec_df.columns = spec_df.columns.str.strip()
else:
    spec_df = pd.DataFrame()

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

if not selected_rooms:
    st.markdown(f"### \U0001F527 פרטי ציוד בכל הקומה {selected_floor}:")
else:
    st.markdown(f"### \U0001F527 פרטי ציוד בחדרים: {', '.join(selected_rooms)}")

main_table = filtered_data[['מספר חדר', 'ID', 'קטגוריה', 'סוג', 'משפחה']].copy()
main_table["נבדק"] = False
main_table["הערה"] = ""

# יצירת טופס לכל שורה
edited_rows = []
for idx, row in main_table.iterrows():
    cols = st.columns([1, 1, 2, 2, 2, 1, 2])
    cols[0].write(row['מספר חדר'])
    cols[1].write(row['ID'])
    cols[2].write(row['קטגוריה'])
    cols[3].write(row['סוג'])
    cols[4].write(row['משפחה'])
    checked = cols[5].checkbox("", key=f"chk_{idx}")
    note = cols[6].text_input("", key=f"note_{idx}")
    edited_rows.append([row['מספר חדר'], row['ID'], row['קטגוריה'], row['סוג'], row['משפחה'], checked, note])

main_table_updated = pd.DataFrame(edited_rows, columns=['מספר חדר', 'ID', 'קטגוריה', 'סוג', 'משפחה', 'נבדק', 'הערה'])
st.dataframe(main_table_updated, use_container_width=True, hide_index=True)

# הורדה ל-CSV
csv_main_table = main_table_updated.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="\U0001F4BE הורד את טבלת הציוד",
    data=csv_main_table,
    file_name="room_equipment_details.csv",
    mime="text/csv"
)

# כפתור שמירה ל-GitHub
st.markdown("---")
if st.button("\U0001F4E5 שמור את העדכונים ל־GitHub"):
    def update_file_to_github(file_path, repo, branch, target_path, token):
        with open(file_path, "rb") as f:
            content = f.read()
        content_b64 = base64.b64encode(content).decode()

        url = f"https://api.github.com/repos/{repo}/contents/{target_path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.get(url, headers=headers, params={"ref": branch})
        sha = response.json()['sha'] if response.status_code == 200 else None

        data = {
            "message": f"Update equipment data for floor {selected_floor}",
            "branch": branch,
            "content": content_b64,
        }
        if sha:
            data["sha"] = sha

        response = requests.put(url, headers=headers, json=data)
        return response.status_code, response.json()

    temp_path = os.path.join(DATA_FOLDER, f"{selected_floor}.csv")
    main_table_updated.to_csv(temp_path, index=False, encoding='utf-8-sig')

    status, result = update_file_to_github(
        file_path=temp_path,
        repo=st.secrets["GITHUB_REPO"],
        branch=st.secrets["GITHUB_BRANCH"],
        target_path=f"{selected_floor}.csv",
        token=st.secrets["GITHUB_TOKEN"]
    )

    if status in [200, 201]:
        st.success("✅ הקובץ עודכן בהצלחה ב־GitHub!")
    else:
        st.error(f"❌ שגיאה בעדכון: {result}")

# טבלת סיכום לפי קטגוריה וסוג
summary_table = filtered_data.groupby(['קטגוריה', 'סוג']).size().reset_index(name='כמות')
if not summary_table.empty:
    title = f"### \U0001F4CA סיכום כמות לפי קטגוריה וסוג – קומה {selected_floor if not selected_rooms else ', '.join(selected_rooms)}"
    st.markdown(title)
    st.dataframe(summary_table, use_container_width=True, hide_index=True)

    csv_summary_table = summary_table.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="\U0001F4BE הורד סיכום לפי קטגוריה וסוג",
        data=csv_summary_table,
        file_name="summary_by_category_type.csv",
        mime="text/csv"
    )

# טבלת סיכום לפי חדרים
summary_by_room = filtered_data.groupby(['מספר חדר', 'קטגוריה', 'סוג']).size().reset_index(name='כמות')
if not summary_by_room.empty:
    st.markdown("### \U0001F4CB סיכום ציוד לפי חדרים:")
    st.dataframe(summary_by_room, use_container_width=True, hide_index=True)

    csv_summary_by_room = summary_by_room.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="\U0001F4BE הורד סיכום לפי חדרים",
        data=csv_summary_by_room,
        file_name="summary_by_room.csv",
        mime="text/csv"
    )

# שיחה עם GPT
st.markdown("---")
st.markdown("### 🤖 שאל את GPT על הציוד שבחרת:")

user_question = st.text_input("מה תרצה לדעת?")

def ask_gpt(prompt, context_df, spec_df=None):
    context = context_df.to_string(index=False)
    spec_context = ""
    if spec_df is not None and not spec_df.empty:
        spec_context = "\n\nמפרט תאורה:\n" + spec_df.to_string(index=False)

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
    gpt_answer = ask_gpt(user_question, summary_by_room, spec_df)
    st.markdown(f"**תשובת GPT:**\n\n{gpt_answer}")

# שלב 5: קריאה לפעולה
st.markdown("---")
st.success("ניתן לבחור קומה נוספת מהתפריט הצדדי כדי להמשיך.")
