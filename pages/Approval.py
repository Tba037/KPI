import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# ----- Connect to Google Sheet -----
@st.cache_resource
def connect_gsheet(x):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "projectkpidashboard.json", scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1bxVq20N1G9UIyek6BVMgpEMOvQJib-j7Jbsfj82KZtE")
    sheet = spreadsheet.worksheet(x)
    return sheet

# ----- Load Google Sheet into DataFrame -----
@st.cache_data
def load_data(x):
    sheet = connect_gsheet(x)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ----- Append new rows to Google Sheet -----
def append_to_database3(new_data):
    sheet_db3 = connect_gsheet("Database3")
    for _, row in new_data.iterrows():
        # Convert Timestamp to string in YYYY-MM-DD format
        timestamp_str = row['Timestamp'].strftime("%Y-%m-%d") if not pd.isna(row['Timestamp']) else ""
        
        sheet_db3.append_row([
            row['Year (YYYY)'],   # Year
            row['Month'],         # Month
            row['Upload'],        # Upload
            timestamp_str         # Timestamp as string
        ])

# ----- Streamlit App -----
def main_app():
    st.set_page_config(page_title="Closing Bank", layout="wide")
    st.title("📊 Closing Bank")

    # Load data
    df_form = load_data("Form Responses 1")
    df_db3 = load_data("Database3")

    # Select year and month
    Year = st.selectbox("Select a year", df_form['Year (YYYY)'].sort_values().unique())
    month_order = ["January", "February", "March", "April", "May", "June","July", "August", "September", "October", "November", "December"]
    months = df_form[df_form['Year (YYYY)'] == Year]['Month'].unique()
    months = [m for m in month_order if m in months]  # keep calendar order
    Month = st.selectbox("Select a month", months)

    # Filter Form Responses
    filtered_form = df_form[(df_form['Month'] == Month) & (df_form['Year (YYYY)'] == Year)].sort_values(by='Timestamp', ascending=False)
    filtered_form['Timestamp'] = pd.to_datetime(filtered_form['Timestamp'], dayfirst=True).dt.date
    st.dataframe(filtered_form)

    # Check Database3 for existing data
    exists = ((df_db3['Year'] == Year) & (df_db3['Month'] == Month)).any()
    if not exists:
        st.warning(f"No data in Database3 for {Month} {Year}. You can approve to add it.")
        if st.button("Approve"):
            append_to_database3(filtered_form)
            st.success(f"Data for {Month} {Year} added to Database3!")
            # Clear cache and force reload
            load_data.clear()  # clears @st.cache_data for load_data
            df_db3 = load_data("Database3")  # reload fresh data
            st.rerun()
    else:
        st.info(f"Data for {Month} {Year} already exists in Database3.")
        st.dataframe(df_db3[(df_db3['Month'] == Month) & (df_db3['Year'] == Year)])

main_app()
