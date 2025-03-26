import streamlit as st
import pandas as pd
from supabase import create_client, Client
from postgrest.exceptions import APIError

st.set_page_config(page_title="IntegriTEX – Referenzdaten erfassen", layout="centered")
st.title("📥 IntegriTEX Referenzdaten erfassen")

# Supabase-Konfiguration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Simulierter Login (nur E-Mail)
st.sidebar.title("Login")
user_email = st.sidebar.text_input("E-Mail")
if not user_email:
    st.warning("Bitte E-Mail-Adresse eingeben, um fortzufahren.")
    st.stop()

st.success(f"Eingeloggt als: {user_email}")

# LOT Nummer und Emission Count
st.subheader("🧾 Proben-Identifikation")
col_id1, col_id2 = st.columns(2)
with col_id1:
    lot_number = st.text_input("LOT Number")
with col_id2:
    emission_count = st.number_input("Emission Count", 0, 100000, step=1)

# Faseranteile
st.subheader("🧵 Faseranteile (in %)")
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        white = st.number_input("White Fiber (%)", 0.0, 100.0, 0.0)
    with col2:
        denim = st.number_input("Denim Fiber (%)", 0.0, 100.0, 0.0)
    with col3:
        black = st.number_input("Black Fiber (%)", 0.0, 100.0, 0.0)
    with col4:
        natural = st.number_input("Natural Fiber (%)", 0.0, 100.0, 0.0)

fiber_sum = white + denim + black + natural
if fiber_sum > 100:
    st.error(f"Die Summe der Fasern darf 100% nicht überschreiten (aktuell: {fiber_sum}%)")

with st.expander("Weitere Faserarten"):
    col1, col2, col3 = st.columns(3)
    with col1:
        cotton = st.number_input("Cotton (%)", 0.0, 100.0, 0.0)
        pet = st.number_input("PET (%)", 0.0, 100.0, 0.0)
    with col2:
        mmcf = st.number_input("MMCF (%)", 0.0, 100.0, 0.0)
        pa = st.number_input("PA (%)", 0.0, 100.0, 0.0)
    with col3:
        acrylic = st.number_input("Acrylic (%)", 0.0, 100.0, 0.0)
        rec_cotton = st.number_input("Recycled Cotton (%)", 0.0, 100.0, 0.0)

# Dosierung
st.subheader("⚙️ Dosierung & Marker")
col1, col2 = st.columns(2)
with col1:
    mastermix = st.number_input("Mastermix Loading (%)", 0.0, 1.0, value=0.1)
with col2:
    enrichment = st.number_input("Enrichment Level (%)", 0.0, 100.0, value=4.1)

marker_ppm = mastermix * enrichment * 100
marker_ratio = st.number_input("Ratio of marker fiber in %", 0.0, 100.0, key="true_marker_percent")
effective_ppm = marker_ppm * (marker_ratio / 100)

# Farbe
st.subheader("🎨 Farbeingabe")
color_col1, color_col2 = st.columns([1, 2])
with color_col1:
    hex_code = st.text_input("HEX Code", value="#D3D3D3")
with color_col2:
    color_preview = st.color_picker("Wähle Farbe", value=hex_code)

# Daten speichern
if st.button("Submit Data"):
    if fiber_sum > 100:
        st.error("Summe der Hauptfasern darf 100% nicht übersteigen.")
    else:
        data = {
            "lot_number": lot_number,
            "emission_count": emission_count,
            "true_marker_percent": marker_ratio,
            "marker_ppm": round(marker_ppm, 2),
            "effective_ppm": round(effective_ppm, 2),
            "color_hex": hex_code,
            "white": white,
            "denim": denim,
            "black": black,
            "natural": natural,
            "cotton": cotton,
            "pet": pet,
            "mmcf": mmcf,
            "pa": pa,
            "acrylic": acrylic,
            "recycled_cotton": rec_cotton,
            "mastermix": mastermix,
            "enrichment": enrichment,
            "user_email": user_email
        }

        try:
            response = supabase.table("reference_samples").insert(data).execute()
            if response.status_code == 201:
                st.success("✅ Datensatz erfolgreich an Supabase übermittelt!")
            else:
                st.error("❌ Fehler beim Speichern in Supabase.")
        except APIError as e:
            st.error(f"Supabase API Error: {e.message if hasattr(e, 'message') else e}")