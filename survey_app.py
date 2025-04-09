import streamlit as st
from streamlit import components
import numpy as np
import pandas as pd
from streamlit_elements import elements, mui, html, nivo
import time
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials

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

# Initialize time options
time_options = [f"{hour}:00" for hour in range(9, 18)]  # 9 AM to 5 PM

# Function to increment date inputs
def add_date():
    st.session_state.num_dates += 1

# Create multiple date inputs based on the counter
availabilities = []
for i in range(st.session_state.num_dates):
    date_label = "Select your availability for my thesis defense" if i == 0 else f"Additional availability #{i}"
    
    # Use columns to place date selector and time selectors side by side
    cols = st.columns([2, 1, 1])
    
    with cols[0]:
        selected_date = st.date_input(
            date_label,
            july_1,  # Default single date instead of range
            july_1,
            july_31,
            format="MM.DD.YYYY",
            key=f"date_input_{i}"
        )
    
    # Time selection for start and end times
    with cols[1]:
        start_time = st.selectbox(
            "Start Time",
            time_options,
            key=f"start_time_{i}"
        )
    
    with cols[2]:
        # Default end time is 1 hour after start time or last option if that would be out of range
        default_end_idx = min(time_options.index(start_time) + 1, len(time_options) - 1) if f"start_time_{i}" in st.session_state else 0
        end_time = st.selectbox(
            "End Time",
            time_options,
            index=default_end_idx,
            key=f"end_time_{i}"
        )
    
    # Store the complete availability info
    availabilities.append({
        "date": selected_date,
        "start_time": start_time,
        "end_time": end_time
    })

# Add button to add more date inputs
st.button("+ Add another time availability", on_click=add_date)
    
# Prepare list of availability ranges as strings
availability_ranges = []
for i, avail in enumerate(availabilities):
    availability_string = f"{avail['date'].strftime('%Y-%m-%d')} from {avail['start_time']} to {avail['end_time']}"
    st.write(f"Option {i+1}: {availability_string}")
    availability_ranges.append(availability_string)

# Load credentials from Streamlit secrets
try:
    # Load credentials from Streamlit secrets
    gcp_service_account = st.secrets["gcp_service_account"]
    
    # Define the scope
    SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    
    # Create credentials using Credentials class directly
    # If the secret is a string (JSON string), convert to dict first
    if isinstance(gcp_service_account, str):
        gcp_service_account = json.loads(gcp_service_account)
        
    credentials = Credentials.from_service_account_info(
        gcp_service_account, 
        scopes=SCOPE
    )
    
    # Authorize the gspread client with the credentials
    client = gspread.authorize(credentials)
    
    # Open the Google Sheets file using its key
    spreadsheet = client.open_by_key("1fa33nvsxwHp4Dc9FK9eGxono5gyemIpO3I36u8nl5kA")
    sheet = spreadsheet.sheet1
    
    st.success("Successfully connected to Google Sheets!")
    
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {type(e).__name__}")
    st.error("Please check your secrets configuration")
    # For debugging locally; don't use in production
    if not st.secrets.get("is_production", False):
        st.error(str(e))
    # Stop execution here to prevent further errors
    st.stop()

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
