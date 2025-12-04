import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import altair as alt
import json
from st_aggrid import AgGrid, GridOptionsBuilder

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
@st.cache_data
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
    sheet_db = connect_gsheet("Database5")
    for _, row in new_data.iterrows():
        sheet_db.append_row([
            row['Month'],        # Upload
            row['Year'],         # Month
            row['Details'],   # Year
            row['Poin']  # Email
        ])

# ----- Streamlit App -----
def main_app():
    st.set_page_config(page_title="Performance", layout="wide")
    st.title("📊 Performance")
    if st.button("Refresh Data"):
        load_data.clear()
        df, df2, df3, df4, df5, df6, df7 = loading_data()
        st.rerun()
    # Load data
    df, df2, df3, df4, df5, df6, df7 = loading_data()
    Year = st.selectbox("Select a year", df['Year'].sort_values().unique())
    month_order = ["January", "February", "March", "April", "May", "June","July", "August", "September", "October", "November", "December"]
    months = df[df['Year'] == Year]['Month'].unique()
    months = [m for m in month_order if m in months]  # keeps calendar order
    Month = st.selectbox("Select a month", months)
    filtered_form = df7[(df7['Month'] == Month) & (df7['Year'] == Year)]
    filtered_form = filtered_form.reset_index()   # <--- Keeps original index as 'index'
    filtered_form.rename(columns={'index': 'row_id'}, inplace=True)
    total_poin = filtered_form["Poin"].sum()
    st.markdown(f"""<div style='text-align: right; font-size: 30px;'>Total Pengurangan Poin Bulan {Month} Tahun {Year} = <u>{total_poin}</u></div>""",unsafe_allow_html=True)
    st.subheader("Details")
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(filtered_form)
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_column("row_id", headerName="ID", width=5)
    gb.configure_column("Month", width=20)
    gb.configure_column("Year", width=20)
    gb.configure_column("Details", width=150)
    gb.configure_column("Poin", width=20)
    grid_options = gb.build()
    # Show interactive table
    grid_response = AgGrid(
        filtered_form,
        gridOptions=grid_options,
        update_mode="MODEL_CHANGED",
        fit_columns_on_grid_load=True,
        height=300
    )
    with st.form("delete_entry_form"):
        # Get selected rows
        selected_rows = grid_response['selected_rows']
        st.subheader("Delete items (Check the Item and Click Delete)")
        submitted = st.form_submit_button("Delete")
        if submitted:
            if selected_rows is not None and len(selected_rows) > 0:
                selected_df = pd.DataFrame(selected_rows)
                # Use row_id to identify exact Google Sheet rows
                delete_indices = selected_df["row_id"].tolist()
                # Convert to Google Sheet row numbers
                gsheet_rows_to_delete = sorted([i + 2 for i in delete_indices], reverse=True)
                sheet = connect_gsheet("Database5")
                for r in gsheet_rows_to_delete:
                    sheet.delete_rows(r)
                load_data.clear()
                df, df2, df3, df4, df5, df6, df7 = loading_data()
                st.success("Entry Deleted!")
                st.rerun()
            else:
                st.warning("No rows selected")
    # ----- Add New Entry -----
    with st.form("add_entry_form", clear_on_submit=True):
        st.subheader("Add Item (Fill in Details and Poin)")
        new_details = st.text_input("Details")
        new_poin = st.number_input("Poin", value=0, min_value=-100, max_value=0)
        submitted = st.form_submit_button("Add")
        if submitted:
            if not new_details:  # Check if new_details is empty
                st.warning("Please fill in the Details field before submitting.")
            else:
                new_row = pd.DataFrame([{
                    "Month": Month,
                    "Year": Year,
                    "Details": new_details,
                    "Poin": new_poin
                }])
                append_to_database(new_row)  # Append to Google Sheet
                load_data.clear()
                df, df2, df3, df4, df5, df6, df7 = loading_data()
                st.success("New entry added!")
                st.rerun()

main_app()