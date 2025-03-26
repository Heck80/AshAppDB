import streamlit as st
from supabase import create_client
from postgrest.exceptions import APIError
from gotrue.errors import AuthApiError

st.set_page_config(page_title="IntegriTEX – Login & Registration", layout="centered")

# Supabase Setup
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Session State init
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

# Login/Signup UI
mode = st.sidebar.radio("🔐 Wähle Modus:", ["Login", "Registrieren"])
email = st.sidebar.text_input("E-Mail")
password = st.sidebar.text_input("Passwort", type="password")

if mode == "Login":
    if st.sidebar.button("Login"):
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = auth_response.user
            st.session_state.token = auth_response.session.access_token
            st.success("✅ Eingeloggt!")
            st.experimental_rerun()
        except AuthApiError:
            st.error("❌ Login fehlgeschlagen. Bitte überprüfe E-Mail & Passwort.")

elif mode == "Registrieren":
    if st.sidebar.button("Konto erstellen"):
        try:
            reg = supabase.auth.sign_up({"email": email, "password": password})
            if reg.user:
                st.success("✅ Registrierung erfolgreich. Bitte jetzt einloggen.")
        except Exception as e:
            st.error(f"❌ Fehler: {e}")

# Wenn eingeloggt → Formular anzeigen
if st.session_state.user and st.session_state.token:
    user = st.session_state.user
    token = st.session_state.token
    supabase = create_client(url, key, access_token=token)

    st.success(f"Angemeldet als {user.email}")
    st.title("📥 Referenzdaten erfassen")

    lot = st.text_input("LOT Number")
    p_white = st.number_input("White Fiber %", 0.0, 100.0, 0.0)
    p_black = st.number_input("Black Fiber %", 0.0, 100.0, 0.0)
    p_denim = st.number_input("Denim Fiber %", 0.0, 100.0, 0.0)
    p_natural = st.number_input("Natural Fiber %", 0.0, 100.0, 0.0)
    cotton = st.number_input("Cotton %", 0.0, 100.0, 0.0)
    mmcf = st.number_input("MMCF %", 0.0, 100.0, 0.0)
    pet = st.number_input("PET %", 0.0, 100.0, 0.0)
    pa = st.number_input("PA %", 0.0, 100.0, 0.0)
    acrylic = st.number_input("Acrylic %", 0.0, 100.0, 0.0)
    rec = st.number_input("Recycled Cotton %", 0.0, 100.0, 0.0)
    mload = st.number_input("Mastermix Loading %", 0.0, 1.0, 0.1)
    enrich = st.number_input("Enrichment %", 0.0, 100.0, 4.0)
    marker = st.number_input("Marker Fiber %", 0.0, 100.0, 0.0)
    ash = st.color_picker("Ash Color", "#D3D3D3")
    count = st.number_input("Emission Count", 0, 999999, 0)
    temp = st.number_input("Furnace Temp °C", 0, 1000, 0)
    time = st.number_input("Furnace Time min", 0, 500, 0)
    scanner = st.text_input("Scanner Setting")

    if st.button("Submit"):
        data = {
            "lot_number": lot,
            "percent_white": p_white,
            "percent_black": p_black,
            "percent_denim": p_denim,
            "percent_natural": p_natural,
            "cotton": cotton,
            "mmcf": mmcf,
            "pet": pet,
            "pa": pa,
            "acrylic": acrylic,
            "recycled_cotton": rec,
            "mastermix_loading": mload,
            "enrichment": enrich,
            "true_marker_percent": marker,
            "ash_color": ash,
            "signal_count": count,
            "furnace_temp": temp,
            "furnace_time": time,
            "scanner_setting": scanner,
            "submitted_by": user.email
        }

        try:
            res = supabase.table("reference_samples").insert(data).execute()
            if res.status_code == 201:
                st.success("✅ Datensatz gespeichert!")
            else:
                st.error("❌ Fehler beim Speichern.")
        except Exception as e:
            st.error(f"Supabase Error: {e}")