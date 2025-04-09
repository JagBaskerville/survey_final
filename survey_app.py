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

# Initialize state to keep track of how many date ranges to show
if 'num_date_ranges' not in st.session_state:
    st.session_state.num_date_ranges = 1
    
# Define time blocks
time_blocks = {
    "Morning (10 AM - 12 PM)": "10 AM - 12 PM",
    "Afternoon (2 PM - 4 PM)": "2 PM - 4 PM",
    "Afternoon (4PM - 6PM)": "4 PM - 6 PM"
}

# Function to increment date ranges
def add_date_range():
    st.session_state.num_date_ranges += 1

# Create multiple date range inputs with time block selections
availabilities = []
for i in range(st.session_state.num_date_ranges):
    st.markdown(f"### Availability Option {i+1}")
    
    # Date range input
    date_label = "Select date range for availability" if i == 0 else f"Additional date range #{i}"
    date_range = st.date_input(
        date_label,
        (july_1, july_1),  # Default
        july_1,
        july_31,
        format="MM.DD.YYYY",
        key=f"date_range_{i}"
    )
    
    # Check if we have a valid date range
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        
        # Calculate all dates in the range
        delta = end_date - start_date
        dates_in_range = [start_date + datetime.timedelta(days=d) for d in range(delta.days + 1)]
        
        if dates_in_range:
            st.write(f"Select time blocks for each date in range ({start_date} to {end_date}):")
            
            # Create columns for dates
            cols = st.columns(min(3, len(dates_in_range)))
            date_time_selections = {}
            
            # For each date, provide time block options
            for j, date in enumerate(dates_in_range):
                col_idx = j % len(cols)
                with cols[col_idx]:
                    st.write(f"**{date.strftime('%b %d, %Y')}**")
                    
                    # Create multiselect for time blocks
                    selected_blocks = st.multiselect(
                        "Select time blocks",
                        options=list(time_blocks.keys()),
                        key=f"time_blocks_{i}_{date}"
                    )
                    
                    if selected_blocks:
                        date_time_selections[date.strftime('%Y-%m-%d')] = [time_blocks[block] for block in selected_blocks]
            
            # Add the complete availability info
            availabilities.append({
                "date_range": f"{start_date} to {end_date}",
                "time_selections": date_time_selections
            })

# Add button to add more date range inputs
st.button("+ Add another date range", on_click=add_date_range)
    
# Prepare list of availability ranges as strings
availability_ranges = []
for i, avail in enumerate(availabilities):
    if avail["time_selections"]:
        date_time_strings = []
        for date, time_blocks in avail["time_selections"].items():
            if time_blocks:
                date_time_strings.append(f"{date}: {', '.join(time_blocks)}")
        
        if date_time_strings:
            availability_string = "; ".join(date_time_strings)
            st.write(f"Option {i+1} selected: {availability_string}")
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
    if not availability_ranges:
        st.error("Please select at least one time block for any date before submitting.")
    else:
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
