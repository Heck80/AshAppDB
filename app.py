
import streamlit as st
from supabase import create_client, Client
import datetime

# --- Supabase Config aus secrets.toml ---
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Reference Sample Entry", layout="wide")
st.title("📄 Reference Sample Entry Form")

# --- Auth: Einloggen oder Registrieren ---
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

        if res.get("error"):
            st.error(f"Auth failed: {res['error']['message']}")
        else:
            st.session_state.user = res.user
            st.success("Logged in successfully!")

# Nur wenn eingeloggt:
if "user" in st.session_state:
    user_email = st.session_state.user.email
    st.success(f"Logged in as: {user_email}")

    with st.form("reference_form"):
        st.subheader("📋 Required Fields")

        lot_number = st.text_input("LOT Number *")
        col1, col2 = st.columns(2)
        with col1:
            percent_natural = st.number_input("Natural Fibers (%) *", min_value=0.0, max_value=100.0, value=0.0)
            percent_black = st.number_input("Black Fibers (%) *", min_value=0.0, max_value=100.0, value=0.0)
        with col2:
            percent_white = st.number_input("White Fibers (%) *", min_value=0.0, max_value=100.0, value=0.0)
            percent_denim = st.number_input("Denim Fibers (%) *", min_value=0.0, max_value=100.0, value=0.0)

        ash_color = st.color_picker("Ash Color *")
        signal_count = st.number_input("Signal (Count) *", min_value=0.0, value=0.0)
        true_marker_percent = st.number_input("True % of Marked Fiber *", min_value=0.0, max_value=100.0, value=0.0)

        st.markdown("---")
        st.subheader("⚙️ Optional Fields")

        cotton = st.number_input("Cotton (%)", min_value=0.0, max_value=100.0, value=None)
        mmcf = st.number_input("MMCF (%)", min_value=0.0, max_value=100.0, value=None)
        pet = st.number_input("PET (%)", min_value=0.0, max_value=100.0, value=None)
        pa = st.number_input("PA (%)", min_value=0.0, max_value=100.0, value=None)
        acrylic = st.number_input("Acrylic (%)", min_value=0.0, max_value=100.0, value=None)
        recycled_cotton = st.number_input("Recycled Cotton (%)", min_value=0.0, max_value=100.0, value=None)
        mastermix_loading = st.number_input("Mastermix Loading (%)", min_value=0.0, value=None)
        enrichment = st.number_input("Enrichment (%)", min_value=0.0, value=None)
        furnace_temp = st.number_input("Furnace Temperature (°C)", min_value=0.0, value=None)
        furnace_time = st.number_input("Furnace Holding Time (hrs)", min_value=0.0, value=None)
        scanner_setting = st.text_input("Scanner Setting")

        submitted = st.form_submit_button("📤 Submit Sample")

        if submitted:
            required_filled = all([lot_number, signal_count, true_marker_percent, ash_color])
            if not required_filled:
                st.error("Please fill in all required fields (*)")
            else:
                data = {
                    "lot_number": lot_number,
                    "percent_natural": percent_natural,
                    "percent_black": percent_black,
                    "percent_white": percent_white,
                    "percent_denim": percent_denim,
                    "ash_color": ash_color,
                    "signal_count": signal_count,
                    "true_marker_percent": true_marker_percent,
                    "cotton": cotton,
                    "mmcf": mmcf,
                    "pet": pet,
                    "pa": pa,
                    "acrylic": acrylic,
                    "recycled_cotton": recycled_cotton,
                    "mastermix_loading": mastermix_loading,
                    "enrichment": enrichment,
                    "furnace_temp": furnace_temp,
                    "furnace_time": furnace_time,
                    "scanner_setting": scanner_setting,
                    "submitted_by": user_email
                }
                res = supabase.table("reference_samples").insert(data).execute()
                if res.data:
                    st.success("Sample successfully submitted! ✅")
                else:
                    st.error("Failed to submit data.")
else:
    st.warning("Please log in to submit data.")
