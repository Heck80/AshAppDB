import streamlit as st
import pandas as pd
from supabase import create_client
from postgrest.exceptions import APIError
from gotrue.errors import AuthApiError
import httpx

st.set_page_config(page_title="IntegriTEX – Login & Registrierung", layout="centered")

# Supabase Setup
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

auth_mode = st.sidebar.radio("🔐 Modus wählen:", ["Login", "Registrieren"])
email = st.sidebar.text_input("E-Mail")
password = st.sidebar.text_input("Passwort", type="password")

if auth_mode == "Login":
    if st.sidebar.button("Login"):
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = auth_response.user
            st.session_state.token = auth_response.session.access_token
            st.success("✅ Login erfolgreich")
            st.experimental_rerun()
        except AuthApiError:
            st.error("❌ Login fehlgeschlagen. E-Mail oder Passwort falsch?")

elif auth_mode == "Registrieren":
    if st.sidebar.button("Konto erstellen"):
        try:
            reg = supabase.auth.sign_up({"email": email, "password": password})
            if reg.user:
                st.success("✅ Registrierung erfolgreich. Bitte jetzt einloggen.")
        except Exception as e:
            st.error(f"❌ Fehler: {e}")

if st.session_state.user and st.session_state.token:
    user = st.session_state.user
    token = st.session_state.token

    # Manuelle Übergabe des Tokens via Header
    headers = {"Authorization": f"Bearer {token}"}
    supabase = create_client(url, key, options={"headers": headers})

    st.title("📥 Referenzdaten eingeben")
    st.success(f"Eingeloggt als: {user.email}")

    lot_number = st.text_input("LOT Number")
    percent_white = st.number_input("White Fiber %", 0.0, 100.0, 0.0)
    percent_black = st.number_input("Black Fiber %", 0.0, 100.0, 0.0)
    percent_denim = st.number_input("Denim Fiber %", 0.0, 100.0, 0.0)
    percent_natural = st.number_input("Natural Fiber %", 0.0, 100.0, 0.0)

    cotton = st.number_input("Cotton %", 0.0, 100.0, 0.0)
    mmcf = st.number_input("MMCF %", 0.0, 100.0, 0.0)
    pet = st.number_input("PET %", 0.0, 100.0, 0.0)
    pa = st.number_input("PA %", 0.0, 100.0, 0.0)
    acrylic = st.number_input("Acrylic %", 0.0, 100.0, 0.0)
    recycled_cotton = st.number_input("Recycled Cotton %", 0.0, 100.0, 0.0)

    mastermix_loading = st.number_input("Mastermix Loading %", 0.0, 1.0, 0.1)
    enrichment = st.number_input("Enrichment %", 0.0, 100.0, 4.0)
    true_marker_percent = st.number_input("Marker Fiber %", 0.0, 100.0, 0.0)
    ash_color = st.color_picker("Ash Color", "#D3D3D3")
    signal_count = st.number_input("Emission Count", 0, 999999, 0)
    furnace_temp = st.number_input("Furnace Temp °C", 0, 1000, 0)
    furnace_time = st.number_input("Furnace Time min", 0, 500, 0)
    scanner_setting = st.text_input("Scanner Setting")

    if st.button("Submit"):
        entry = {
            "lot_number": lot_number,
            "percent_white": percent_white,
            "percent_black": percent_black,
            "percent_denim": percent_denim,
            "percent_natural": percent_natural,
            "cotton": cotton,
            "mmcf": mmcf,
            "pet": pet,
            "pa": pa,
            "acrylic": acrylic,
            "recycled_cotton": recycled_cotton,
            "mastermix_loading": mastermix_loading,
            "enrichment": enrichment,
            "true_marker_percent": true_marker_percent,
            "ash_color": ash_color,
            "signal_count": signal_count,
            "furnace_temp": furnace_temp,
            "furnace_time": furnace_time,
            "scanner_setting": scanner_setting,
            "submitted_by": user.email
        }

        try:
            res = supabase.table("reference_samples").insert(entry).execute()
            if res.status_code == 201:
                st.success("✅ Datensatz erfolgreich gespeichert!")
            else:
                st.error("❌ Fehler beim Speichern.")
        except Exception as e:
            st.error(f"Supabase Error: {e}")