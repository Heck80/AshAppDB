
import streamlit as st
from supabase import create_client, Client
from gotrue.errors import AuthApiError

# Supabase-Konfiguration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Reference Sample Entry", layout="wide")
st.title("📄 Reference Sample Entry")

# Auth Bereich
with st.sidebar:
    st.header("🔐 Login / Sign up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    action = st.radio("Choose action", ["Login", "Sign up"])

    if st.button("Continue"):
        if not email or not password:
            st.warning("Please provide both email and password.")
        elif len(password) < 6:
            st.warning("Password must be at least 6 characters.")
        else:
            try:
                if action == "Sign up":
                    res = supabase.auth.sign_up({"email": email, "password": password})
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})

                if res.user:
                    st.session_state.user = res.user
                    st.success("Successfully logged in!")
                else:
                    st.error("Login failed. Please check credentials.")

            except AuthApiError as e:
                st.error("Authentication error:")
                st.exception(e)
            except Exception as e:
                st.error("Unexpected error:")
                st.exception(e)

if "user" in st.session_state:
    user_email = st.session_state.user.email
    st.success(f"Logged in as: {user_email}")

    with st.form("sample_form"):
        st.subheader("🧪 Reference Sample Data")

        lot_number = st.text_input("LOT Number *")
        signal_count = st.number_input("Signal Count *", min_value=0.0)
        true_marker_percent = st.number_input("True % of Marked Fiber *", min_value=0.0)
        ash_color = st.color_picker("Ash Color *")

        percent_natural = st.number_input("Natural Fibers (%)", min_value=0.0)
        percent_black = st.number_input("Black Fibers (%)", min_value=0.0)
        percent_white = st.number_input("White Fibers (%)", min_value=0.0)
        percent_denim = st.number_input("Denim Fibers (%)", min_value=0.0)

        cotton = st.number_input("Cotton (%)", min_value=0.0)
        mmcf = st.number_input("MMCF (%)", min_value=0.0)
        pet = st.number_input("PET (%)", min_value=0.0)
        pa = st.number_input("PA (%)", min_value=0.0)
        acrylic = st.number_input("Acrylic (%)", min_value=0.0)
        recycled_cotton = st.number_input("Recycled Cotton (%)", min_value=0.0)

        mastermix_loading = st.number_input("Mastermix Loading (%)", min_value=0.0)
        enrichment = st.number_input("Enrichment (%)", min_value=0.0)
        furnace_temp = st.number_input("Furnace Temperature (°C)", min_value=0.0)
        furnace_time = st.number_input("Furnace Holding Time (hrs)", min_value=0.0)

        scanner_setting = st.text_input("Scanner Setting")

        submitted = st.form_submit_button("Submit Sample")

        if submitted:
            required = all([lot_number, signal_count, true_marker_percent, ash_color])
            if not required:
                st.warning("Please fill in all required fields.")
            else:
                try:
                    data = {
                        "lot_number": lot_number,
                        "percent_natural": int(percent_natural),
                        "percent_black": int(percent_black),
                        "percent_white": int(percent_white),
                        "percent_denim": int(percent_denim),
                        "cotton": int(cotton),
                        "mmcf": int(mmcf),
                        "pet": int(pet),
                        "pa": int(pa),
                        "acrylic": int(acrylic),
                        "recycled_cotton": int(recycled_cotton),
                        "mastermix_loading": float(mastermix_loading),
                        "enrichment": float(enrichment),
                        "ash_color": ash_color,
                        "signal_count": float(signal_count),
                        "furnace_temp": float(furnace_temp),
                        "furnace_time": float(furnace_time),
                        "scanner_setting": scanner_setting,
                        "true_marker_percent": float(true_marker_percent),
                        "submitted_by": user_email
                    }

                    res = supabase.table("reference_samples").insert(data).execute()
                    if res.data:
                        st.success("✅ Sample successfully submitted!")
                    else:
                        st.error("⚠️ Something went wrong. Check the form or try again.")
                except Exception as e:
                    st.error("Insert error:")
                    st.exception(e)
else:
    st.info("Please log in to submit reference data.")
