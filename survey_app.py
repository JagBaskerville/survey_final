import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

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
st.markdown("<h2><b>Committee basic information</b></h2>", unsafe_allow_html=True)
name_e = st.text_input("Your full name (English):")
name_c = st.text_input("Your full name (Chinese):")
position = st.text_input("Your Current Position and Unit (\u73fe\u4efb\u6216\u66fe\u4efb\u8077\u52d9\u53ca\u55ae\u4f4d):")

# Asking availability in July
st.markdown("<h2><b>Schedule available in July 2025</b></h2>", unsafe_allow_html=True)

# Set up the date range for July
july_1 = datetime.date(datetime.datetime.now().year, 7, 1)
july_31 = datetime.date(datetime.datetime.now().year, 7, 31)

st.markdown("### Select a range of dates and specify time slots for each day")

# Step 1: Date range input
date_range = st.date_input(
    "Select your available date range",
    value=(july_1, july_1),
    min_value=july_1,
    max_value=july_31
)

# Step 2: Define time slot options
time_options = ["Morning (08:00–12:00)", "Afternoon (13:00–17:00)", "Evening (18:00–21:00)"]

availability_ranges = []

# Step 3: Generate each date in the selected range and collect time slots
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    if start_date <= end_date:
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + datetime.timedelta(days=i)
            times = st.multiselect(
                f"Available time slots on {day}",
                time_options,
                key=f"day_{i}"
            )
            if times:
                availability_ranges.append(f"{day} - {', '.join(times)}")

# Load credentials from Streamlit secrets
try:
    gcp_service_account = st.secrets["gcp_service_account"]

    SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    if isinstance(gcp_service_account, str):
        gcp_service_account = json.loads(gcp_service_account)

    credentials = Credentials.from_service_account_info(
        gcp_service_account,
        scopes=SCOPE
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key("1fa33nvsxwHp4Dc9FK9eGxono5gyemIpO3I36u8nl5kA")
    sheet = spreadsheet.sheet1

    st.success("Successfully connected to Google Sheets!")

except Exception as e:
    st.error(f"Error connecting to Google Sheets: {type(e).__name__}")
    if not st.secrets.get("is_production", False):
        st.error(str(e))
    st.stop()

# Submit data to Google Sheet
if st.button("Submit your availabilities"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_row = [
        name_e,
        name_c,
        position,
        "; ".join(availability_ranges),
        timestamp
    ]

    sheet.append_row(data_row)
    st.success("Your response has been successfully saved!")
