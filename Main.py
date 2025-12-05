import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import altair as alt
import json
import time
import io

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

# ----- Calculate KPI 1 (Alokasi AR) -----
def calculate_kpi_ar(df, Month, Year):
    df = df[(df['Month'] == Month) & (df['Year'] == Year)]
    target = df['DocNum'].count()
    realisasi = df['Poin'].sum()
    percentage = (realisasi / target) * 100 if target != 0 else 0
    poin = 100
    final = poin * (percentage / 100)
    
    return pd.DataFrame({
        "Target": [target],
        "Realisasi": [realisasi],
        "%": [round(percentage, 2)],
        "Poin": [poin],
        "Final": [round(final, 2)]
    }, index=["Alokasi Ar Tepat Waktu (Daily) H+1 Tanggal Uang Masuk"])

# ----- Calculate KPI 2 (Cancelled Incoming) -----
def calculate_kpi_cancel(df, Month, Year):
    df = df[(df['Month'] == Month) & (df['Year'] == Year)]
    target = 0
    realisasi = df[df['Canceled'] == "Y"]['DocNum'].count()
    total_docnum = df['DocNum'].count()
    percentage = ((total_docnum - realisasi) / total_docnum) * 100 if total_docnum != 0 else 0
    poin = 100
    final = poin * (percentage / 100)
    
    return pd.DataFrame({
        "Target": [target],
        "Realisasi": [realisasi],
        "%": [round(percentage, 2)],
        "Poin": [poin],
        "Final": [round(final, 2)]
    }, index=["Cancel Icomming (Monthly) Pengurangan Setiap Adanya Cancel Incomming"])

def calculate_kpi_tagih_invoice(df2, Month, Year):
    df2 = df2[(df2['Month'] == Month) & (df2['Year'] == Year)]
    target = df2['Document Number'].count()
    realisasi = df2['Poin'].sum()
    percentage = (realisasi / target) * 100 if target != 0 else 0
    poin = 100
    final = poin * (percentage / 100)
    
    return pd.DataFrame({
        "Target": [target],
        "Realisasi": [realisasi],
        "%": [round(percentage, 2)],
        "Poin": [poin],
        "Final": [round(final, 2)]
    }, index=["Keberhasilan Penagihan (Khusus Tempo) %Invoice Jt >14 Hari Setiap Bulannya"])

def calculate_kpi_closing_bank(df3, Month, Year):
    df3 = df3[(df3['Month'] == Month) & (df3['Year'] == Year)]
    # Convert Timestamp column to datetime
    df3['Timestamp'] = pd.to_datetime(df3['Timestamp'], errors='coerce', dayfirst=True)
    # Target deadline
    target = pd.to_datetime(f"10 {Month} {Year}", format="%d %B %Y")
    target = target + pd.DateOffset(months=1)
    # Take the latest closing timestamp for the selected month
    if df3['Timestamp'].notna().any():
        realisasi = df3['Timestamp'].max()
    else:
        realisasi = "Butuh Approval"
    if realisasi is not "Butuh Approval":
        selisih = (pd.to_datetime(realisasi).date() - pd.to_datetime(target).date()).days
        percentage = 100 if selisih <= 0 else 0
    else:
        selisih = "Butuh Approval"
        percentage = 0
    poin = 100
    final = poin * (percentage / 100)
    
    return pd.DataFrame({
        "Target": [target],
        "Realisasi": [realisasi],
        "%": [round(percentage, 2)],
        "Poin": [poin],
        "Final": [round(final, 2)],
    }, index=["Closing Bank (Credit) Tepat Waktu (Monthly) Setiap Tanggal 10 Bulan Berikutnya"])

def calculate_kpi_filing_ke_accounting(df5, Month, Year):
    df5 = df5[(df5['Month'] == Month) & (df5['Year'] == Year)]
    # Convert Timestamp column to datetime
    df5['Timestamp'] = pd.to_datetime(df5['Timestamp'], errors='coerce', dayfirst=True)
    # Target deadline
    target = pd.to_datetime(f"1 {Month} {Year}", format="%d %B %Y") + pd.offsets.MonthEnd(0)
    # Take the latest closing timestamp for the selected month
    if df5['Timestamp'].notna().any():
        realisasi = df5['Timestamp'].max()
    else:
        realisasi = "Butuh Approval"
    if realisasi is not "Butuh Approval":
        selisih = (pd.to_datetime(realisasi).date() - pd.to_datetime(target).date()).days
        percentage = 100 if selisih <= 0 else 0
    else:
        selisih = "Butuh Approval"
        percentage = 0
    poin = 100
    final = poin * (percentage / 100)
    
    return pd.DataFrame({
        "Target": [target],
        "Realisasi": [realisasi],
        "%": [round(percentage, 2)],
        "Poin": [poin],
        "Final": [round(final, 2)],
    }, index=["Serah Terima Dokumen Filing Ke Accounting 1 Bulan Setelah Periode Berjalan"])

def calculate_kpi_performance(df7, Month, Year):
    df7 = df7[(df7['Month'] == Month) & (df7['Year'] == Year)]
    target = 100
    realisasi = target + df7["Poin"].sum()
    percentage = (realisasi / target) * 100 if target != 0 else 0
    poin = 100
    final = poin * (percentage / 100)
    
    return pd.DataFrame({
        "Target": [target],
        "Realisasi": [realisasi],
        "%": [round(percentage, 2)],
        "Poin": [poin],
        "Final": [round(final, 2)]
    }, index=["Pelanggaran Sop Kerja Poin Pengurangan Nilai Kpi Setiap Pelanggaran Yang Timbul"])

def calculate_total_kpi(kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, Month, Year):
    return pd.DataFrame({
        "Final": [kpi1["Final"][0] + kpi2["Final"][0] + kpi3["Final"][0] + kpi4["Final"][0] + kpi5["Final"][0] + kpi6["Final"][0]]
    }, index=[f"TOTAL KPI {Month} {Year}"])

# ----- Streamlit App -----
def main_app():
    # Set wide layout
    st.set_page_config(page_title="KPI Indicator", layout="wide")
    st.title("📊 KPI Indicator")
    if st.button("Refresh Data"):
        time.sleep(1)
        st.cache_data.clear()
        df, df2, df3, df4, df5, df6, df7 = loading_data()
        st.rerun()
    df, df2, df3, df4, df5, df6, df7 = loading_data()
    Year = st.selectbox("Select a year", df['Year'].sort_values().unique())
    month_order = ["January", "February", "March", "April", "May", "June","July", "August", "September", "October", "November", "December"]
    months = df[df['Year'] == Year]['Month'].unique()
    months = [m for m in month_order if m in months]  # keeps calendar order
    Month = st.selectbox("Select a month", months)
    # Calculate KPIs
    kpi1 = calculate_kpi_ar(df, Month, Year)
    kpi2 = calculate_kpi_cancel(df, Month, Year)
    kpi3 = calculate_kpi_tagih_invoice(df2, Month, Year)
    kpi4 = calculate_kpi_closing_bank(df3, Month, Year)
    kpi5 = calculate_kpi_filing_ke_accounting(df5, Month, Year)
    kpi6 = calculate_kpi_performance(df7, Month, Year)
    total = calculate_total_kpi(kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, Month, Year)
    kpi_table = pd.concat([kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, total])
    # % progress bars
    st.subheader("KPI Indicator")
    kpi_bar = pd.concat([kpi1, kpi2, kpi3, kpi4, kpi5, kpi6])
    for idx, row in kpi_bar.iterrows():
        col1, col2, col3 = st.columns([5, 5, 2])  # adjust column widths
        with col1:
            st.write(f"**{idx}**")
        with col2:
            progress_value = int(min(max(row['%'], 0), 100))  # cap between 0-100
            st.progress(progress_value)
        with col3:
            st.write(f"Final: {row['Final']}")
    # Show combined KPI table
    st.dataframe(kpi_table)
    # Create an in-memory output file for Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:kpi_table.to_excel(writer, index=True, sheet_name="KPI")
    # Rewind the buffer
    output.seek(0)
    # Download button
    st.download_button(
        label="Download KPI Table (Excel)",
        data=output,
        file_name=f"KPI_{Month}_{Year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

main_app()