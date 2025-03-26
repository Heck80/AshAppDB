import streamlit as st
import pandas as pd
from supabase import create_client
from postgrest.exceptions import APIError
from gotrue.errors import AuthApiError

st.set_page_config(page_title="IntegriTEX – Auth & Daten", layout="centered")

# Supabase setup
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Auth-Status initialisieren
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

# Login & Registrierung
auth_mode = st.sidebar.radio("🔐 Auth-Modus wählen:", ["Login", "Registrierung"])

email = st.sidebar.text_input("E-Mail")
password = st.sidebar.text_input("Passwort", type="password")

if auth_mode == "Login":
    if st.sidebar.button("Login"):
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if auth_response.user:
                st.session_state.user = auth_response.user
                st.session_state.token = auth_response.session.access_token
                st.success("✅ Login erfolgreich!")
                st.experimental_rerun()
        except AuthApiError:
            st.error("❌ Login fehlgeschlagen. Bitte Zugangsdaten prüfen.")

elif auth_mode == "Registrierung":
    if st.sidebar.button("Konto erstellen"):
        try:
            reg = supabase.auth.sign_up({"email": email, "password": password})
            if reg.user:
                st.success("✅ Registrierung erfolgreich – du kannst dich jetzt einloggen.")
        except Exception as e:
            st.error(f"Fehler bei Registrierung: {e}")

# Wenn eingeloggt → Dateneingabe
if st.session_state.user:
    user = st.session_state.user
    access_token = st.session_state.token
    supabase = create_client(url, key, access_token=access_token)

    st.success(f"Eingeloggt als {user.email}")
    st.title("📥 Referenzdaten eingeben")

    lot_number = st.text_input("LOT Number")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        percent_white = st.number_input("White Fiber (%)", 0.0, 100.0, 0.0)
    with col2:
        percent_black = st.number_input("Black Fiber (%)", 0.0, 100.0, 0.0)
    with col3:
        percent_denim = st.number_input("Denim Fiber (%)", 0.0, 100.0, 0.0)
    with col4:
        percent_natural = st.number_input("Natural Fiber (%)", 0.0, 100.0, 0.0)

    fiber_sum = percent_white + percent_black + percent_denim + percent_natural
    if fiber_sum > 100:
        st.warning(f"⚠️ Die Summe der Fasern beträgt {fiber_sum}% (max. 100%)")

    with st.expander("Weitere Fasertypen"):
        cotton = st.number_input("Cotton (%)", 0.0, 100.0, 0.0)
        mmcf = st.number_input("MMCF (%)", 0.0, 100.0, 0.0)
        pet = st.number_input("PET (%)", 0.0, 100.0, 0.0)
        pa = st.number_input("PA (%)", 0.0, 100.0, 0.0)
        acrylic = st.number_input("Acrylic (%)", 0.0, 100.0, 0.0)
        recycled_cotton = st.number_input("Recycled Cotton (%)", 0.0, 100.0, 0.0)

    mastermix_loading = st.number_input("Mastermix Loading (%)", 0.0, 1.0, 0.1)
    enrichment = st.number_input("Enrichment (%)", 0.0, 100.0, 4.0)
    true_marker_percent = st.number_input("Ratio of marker fiber (%)", 0.0, 100.0, 0.0)

    ash_color = st.color_picker("Farbe (Ash Color RGB/HEX)", "#D3D3D3")
    signal_count = st.number_input("Emission Count", 0, 100000, step=1)
    furnace_temp = st.number_input("Furnace Temp (°C)", 0, 1000, step=1)
    furnace_time = st.number_input("Furnace Time (min)", 0, 500, step=1)
    scanner_setting = st.text_input("Scanner Setting")

    if st.button("Submit Data"):
        if fiber_sum > 100:
            st.error("❌ Die Fasersumme darf 100% nicht überschreiten.")
        else:
            try:
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
                response = supabase.table("reference_samples").insert(entry).execute()
                if response.status_code == 201:
                    st.success("✅ Datensatz erfolgreich gespeichert!")
                else:
                    st.error("❌ Fehler beim Speichern in Supabase.")
            except APIError as e:
                st.error(f"Supabase API Error: {e}")