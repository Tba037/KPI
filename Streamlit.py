import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---- Connect to Google Sheets ----
@st.cache_resource
def connect_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "projectkpidashboard.json", scope
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key("1bxVq20N1G9UIyek6BVMgpEMOvQJib-j7Jbsfj82KZtE")
    sheet = spreadsheet.worksheet("User")
    return sheet

def check_credentials(username, password, sheet):
    records = sheet.get_all_records()

    for row in records:
        if str(row.get("username")) == username and str(row.get("password")) == password:
            return True
    return False


# ---- Callback: only sets a flag ----
def trigger_login():
    st.session_state.do_login = True


# ---- Session setup ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "do_login" not in st.session_state:
    st.session_state.do_login = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""


def login_page():
    st.title("🔐 Login")

    st.text_input("Username", key="username")
    st.text_input(
        "Password",
        type="password",
        key="password",
        on_change=trigger_login,   # ENTER here triggers login safely
    )

    st.button("Login", on_click=trigger_login)

    if st.session_state.login_error:
        st.error(st.session_state.login_error)


def main_app():
    st.title("🎉 Welcome!")
    st.write("You are logged in using Google Sheets authentication.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.do_login = False
        st.session_state.login_error = ""
        st.rerun()


# ---- MAIN EXECUTION ----

# 1. If login was triggered (ENTER or button)
if st.session_state.do_login:
    sheet = connect_gsheet()
    username = st.session_state.username
    password = st.session_state.password

    if check_credentials(username, password, sheet):
        st.session_state.logged_in = True
        st.session_state.login_error = ""
    else:
        st.session_state.login_error = "Invalid username or password"

    st.session_state.do_login = False
    st.rerun()   # <-- SAFE. Not inside callback.


# 2. Page routing
if st.session_state.logged_in:
    main_app()
else:
    login_page()