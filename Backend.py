import streamlit as st

#SetupPage
Closing_Bank = st.Page(
     page="Closing Bank.py",
     title="Closing Bank",
)
Filing_Accounting = st.Page(
     page="Filing Accounting.py",
     title="Filing Accounting",
)
Performance = st.Page(
     page="Performance.py",
     title="Performance",
     default=True,
)

pg = st.navigation({"Choose": [Performance, Closing_Bank, Filing_Accounting]})
pg.run()