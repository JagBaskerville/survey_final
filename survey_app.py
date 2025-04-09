import streamlit as st
from streamlit import components
import numpy as np
import pandas as pd
from streamlit_elements import elements, mui, html, nivo
import time
import datetime
import gspread
from google.oauth2.service_account import Credentials

# Load credentials from Streamlit secrets
gcp_service_account = st.secrets["gcp_service_account"]

# Define the scope
SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

# Create credentials from the secret dictionary
credentials = service_account.Credentials.from_service_account_info(gcp_service_account)

# Authorize the gspread client with the credentials
client = gspread.authorize(credentials)

# Open the Google Sheets file using its key
spreadsheet = client.open_by_key("1jgkEczK7FkZqGTes6cOYG_kJVCMa6EmiE89AUhnc4vA")
sheet = spreadsheet.sheet1

# Set app title
st.set_page_config(
    page_title="survey_time",
    layout="wide"
)

# Layout
st.title("Availability time of committee members")
st.markdown("""
    <div>
        <h3>Schedule thesis defense</h3>
    </div>
    """, unsafe_allow_html=True)

# Add question to fill in (name, position and Unit)
# 01. Name 
st.markdown("<h2><b>Committee basic information</b></h2>", unsafe_allow_html=True)
name_e = st.text_input("Your full name (English):")
name_c = st.text_input("Your full name (Chinese):")
position = st.text_input("Your Current Position and Unit (現任或曾任職務及單位):")

# 02. Asking availability in July
st.markdown("<h2><b>Schedule available in July 2025</b></h2>", unsafe_allow_html=True)

# Set up the date range for July
today = datetime.datetime.now()
july_1 = datetime.date(today.year, 7, 1)
july_31 = datetime.date(today.year, 7, 31)

# Initialize state to keep track of how many date inputs to show
if 'num_dates' not in st.session_state:
    st.session_state.num_dates = 1

# Function to increment date inputs
def add_date():
    st.session_state.num_dates += 1

# Create multiple date inputs based on the counter
availabilities = []
for i in range(st.session_state.num_dates):
    date_label = "Select your availability for my thesis defense" if i == 0 else f"Additional availability #{i}"
    date_input = st.date_input(
        date_label,
        (july_1, july_1),  # Default
        july_1,
        july_31,
        format="MM.DD.YYYY",
        key=f"date_input_{i}"
    )
    availabilities.append(date_input)

# Add button to add more date inputs
st.button("+ Add another time availability", on_click=add_date)
    
# Prepare list of availability ranges as strings
availability_ranges = []
for i, dates in enumerate(availabilities):
    if isinstance(dates, tuple) and len(dates) == 2:
        st.write(f"Option {i+1}: {dates[0]} to {dates[1]}")
        availability_ranges.append(f"{dates[0]} to {dates[1]}")

if st.button("Submit your availabilities"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_row = [
        name_e,
        name_c,
        position,
        "; ".join(availability_ranges),
        timestamp
    ]

    # Write to Google Sheet
    sheet.append_row(data_row)
    st.success("Your response has been successfully saved!")
