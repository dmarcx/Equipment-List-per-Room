import streamlit as st
import pandas as pd
import os

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

# שלב 3: הצגת רשימת חדרים בטבלה
room_numbers = sorted(df['מספר חדר'].unique())
st.markdown(f"### \U0001F4CD חדרים זמינים בקומה {selected_floor}:")

# הצגה בטבלה של 8 חדרים בכל שורה
for i in range(0, len(room_numbers), 8):
    row = "\t".join(str(room) for room in room_numbers[i:i+8])
    st.code(row, language='')

# Sidebar המשך בחירה
with st.sidebar:
    selected_room = st.selectbox("בחר חדר להצגת הציוד:", room_numbers)

    room_data = df[df['מספר חדר'] == selected_room]

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

st.markdown(f"### \U0001F527 פרטי ציוד בחדר {selected_room}:")
st.dataframe(filtered_data[['ID', 'קטגוריה', 'סוג', 'משפחה']], use_container_width=True, hide_index=True)

# כפתור להורדת הציוד לאקסל
csv_data = filtered_data[['ID', 'קטגוריה', 'סוג', 'משפחה']].to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="\U0001F4BE הורד לקובץ Excel",
    data=csv_data,
    file_name=f"room_{selected_room}_equipment.csv",
    mime="text/csv"
)

# שלב 5: קריאה לפעולה
st.markdown("---")
st.success("ניתן לבחור קומה נוספת מהתפריט הצדדי כדי להמשיך.")
