
import streamlit as st
from supabase import create_client, Client
import json

# Supabase-Konfiguration aus secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="App1 Debug Mode", layout="wide")
st.title("🐞 Debug Mode – Reference Sample Entry")

# Login-Funktion
with st.sidebar:
    st.header("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    login_mode = st.radio("Action", ["Login", "Sign up"])

    if st.button("Continue"):
        if login_mode == "Sign up":
            res = supabase.auth.sign_up({"email": email, "password": password})
        else:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})

        if res.user is None:
            st.error("Authentication failed.")
        else:
            st.session_state.user = res.user
            st.success("Logged in successfully!")

if "user" in st.session_state:
    user_email = st.session_state.user.email
    st.success(f"Logged in as: {user_email}")

    st.subheader("📝 Sample Data Entry (Debug Mode)")
    with st.form("form"):
        lot_number = st.text_input("LOT Number *")
        signal_count = st.number_input("Signal Count *", min_value=0.0)
        true_marker_percent = st.number_input("True % of Marked Fiber *", min_value=0.0, max_value=100.0)
        ash_color = st.color_picker("Ash Color *")
        scanner_setting = st.text_input("Scanner Setting")

        submitted = st.form_submit_button("Submit")

        if submitted:
            data = {
                "lot_number": lot_number,
                "percent_natural": 100.0,
                "percent_black": 0.0,
                "percent_white": 0.0,
                "percent_denim": 0.0,
                "cotton": 0.0,
                "mmcf": 0.0,
                "pet": 0.0,
                "pa": 0.0,
                "acrylic": 0.0,
                "recycled_cotton": 0.0,
                "mastermix_loading": 0.0,
                "enrichment": 0.0,
                "ash_color": ash_color,
                "signal_count": signal_count,
                "furnace_temp": 0.0,
                "furnace_time": 0.0,
                "scanner_setting": scanner_setting,
                "true_marker_percent": true_marker_percent,
                "submitted_by": user_email
            }

            st.code(data, language='json')

            try:
                res = supabase.table("reference_samples").insert(data).execute()
                st.success("Insert submitted.")
                st.write("🔁 Full response:")
                st.write(res)
            except Exception as e:
                st.error("❌ Exception during Supabase insert:")
                st.exception(e)
else:
    st.info("Please log in first to submit.")
