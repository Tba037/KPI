import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import altair as alt
import json
import time

# ----- Connect to Google Sheet -----
@st.cache_resource
def connect_gsheet(x):
    creds_dict = st.secrets["projectkpidashboard"]  # read secret
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1bxVq20N1G9UIyek6BVMgpEMOvQJib-j7Jbsfj82KZtE")
    sheet = spreadsheet.worksheet(x)
    return sheet

# ----- Load Google Sheet into DataFrame -----
def load_data(x):
    sheet = connect_gsheet(x)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

@st.cache_data
def loading_data():
    df = load_data("Database")
    df2 = load_data("Database2")
    df3 = load_data("Database3")
    df4 = load_data("Form Responses 1")
    df5 = load_data("Database4")
    df6 = load_data("Form Responses 2")
    df7 = load_data("Database5")
    return df, df2, df3, df4, df5, df6, df7

# ----- Append new rows to Google Sheet -----
def append_to_database(new_data):
    sheet_db = connect_gsheet("Database4")
    for _, row in new_data.iterrows():
        # Convert Timestamp to string in YYYY-MM-DD format
        timestamp_str = "" if pd.isna(row['Timestamp']) else str(row['Timestamp'])
        sheet_db.append_row([
            timestamp_str,        # Timestamp
            row['Upload'],        # Upload
            row['Month'],         # Month
            row['Year (YYYY)'],   # Year
            row['Email Address']  # Email
        ])

# ----- Streamlit App -----
def main_app():
    st.set_page_config(page_title="Filing Accounting", layout="wide")
    st.title("📊 Filing Accounting")
    if st.button("Refresh Data"):
        time.sleep(1)
        st.cache_data.clear()
        df, df2, df3, df4, df5, df6, df7 = loading_data()
        st.rerun()
    # Load data
    df, df2, df3, df4, df5, df6, df7 = loading_data()
    # Select year and month
    Year = st.selectbox("Select a year", df6['Year (YYYY)'].sort_values().unique())
    month_order = ["January", "February", "March", "April", "May", "June","July", "August", "September", "October", "November", "December"]
    months = df6[df6['Year (YYYY)'] == Year]['Month'].unique()
    months = [m for m in month_order if m in months]  # keep calendar order
    Month = st.selectbox("Select a month", months)
    # Filter Form Responses
    filtered_form = df6[(df6['Month'] == Month) & (df6['Year (YYYY)'] == Year)].sort_values(by='Timestamp', ascending=False)
    # Ensure Timestamp is in datetime format
    filtered_form['Timestamp'] = pd.to_datetime(filtered_form['Timestamp'])
    # Format the Timestamp column
    filtered_form['Timestamp'] = filtered_form['Timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
    # Check Database5 for existing data
    exists = ((df5['Year'] == Year) & (df5['Month'] == Month)).any()
    if not exists:
        st.warning(f"No data in Database5 for {Month} {Year}. You can approve to add it.")
        # Pretty table layout
        for idx, row in filtered_form.iterrows():
            row_exists = (
                (df5["Timestamp"] == str(row['Timestamp'])) &
                (df5["Upload"] == row["Upload"]) &
                (df5["Email Address"] == row["Email Address"])
            ).any()
            col1, col2, col3, col4 = st.columns([2, 4, 3, 2])
            with col1:
                st.write(row["Timestamp"])
            with col2:
                st.write(row["Upload"])
            with col3:
                st.write(row["Email Address"])
            with col4:
                if row_exists:
                    st.success("Approved ✓")
                else:
                    if st.button("Approve", key=f"approve_{idx}"):
                        append_to_database(pd.DataFrame([row]))
                        st.cache_data.clear()
                        df, df2, df3, df4, df5, df6, df7 = loading_data()
                        st.success("Row added!")
                        st.rerun()
    else:
        st.info(f"Data for {Month} {Year} already exists in Database5.")
        filtered_df = df5.loc[(df5['Month'] == Month) & (df5['Year'] == Year), ["Timestamp", "Upload", "Email Address"]]
        for i, row in filtered_df.iterrows():
            col1, col2, col3 = st.columns([2, 4, 3])
            with col1:
                st.write(row["Timestamp"])
            with col2:
                st.write(row["Upload"])
            with col3:
                st.write(row["Email Address"])

main_app()