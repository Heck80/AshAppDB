import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="IntegriTEX – Referenzdaten erfassen", layout="centered")
st.title("📥 IntegriTEX Referenzdaten erfassen")

# Supabase-Konfiguration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Registrierungshinweis (nur einmal zeigen)
if "show_registration_info" not in st.session_state:
    st.session_state.show_registration_info = True

if st.session_state.show_registration_info:
    st.info("Please confirm your email address via the link we sent you. You can only log in once it's verified.")
    st.session_state.show_registration_info = False

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

st.subheader("⚙️ Dosierung")
col1, col2 = st.columns(2)
with col1:
    mastermix = st.number_input("Mastermix Loading (%)", 0.0, 1.0, value=0.1)
with col2:
    enrichment = st.number_input("Enrichment Level (%)", 0.0, 100.0, value=4.1)

st.subheader("📌 Markierungsanteil")
marker_ratio = st.number_input("Ratio of marker fiber in %", 0.0, 100.0, key="true_marker_percent")

st.subheader("🎨 Farbeingabe")
color_col1, color_col2 = st.columns([1, 2])
with color_col1:
    hex_code = st.text_input("HEX Code", value="#D3D3D3")
with color_col2:
    color_preview = st.color_picker("Wähle Farbe", value=hex_code)

if st.button("Submit Data"):
    if fiber_sum > 100:
        st.error("Summe der Hauptfasern darf 100% nicht übersteigen.")
    else:
        data = {
            "true_marker_percent": marker_ratio,
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
        }
        response = supabase.table("reference_samples").insert(data).execute()
        if response.status_code == 201:
            st.success("✅ Datensatz erfolgreich an Supabase übermittelt!")
        else:
            st.error("❌ Fehler beim Speichern in Supabase.")

# 🔍 Daten anzeigen, löschen, CSV export/import
st.subheader("📋 Datenbank-Ansicht")
response = supabase.table("reference_samples").select("*").execute()
if response.data:
    df = pd.DataFrame(response.data)
    st.dataframe(df)

    # Einträge löschen
    to_delete = st.multiselect("IDs auswählen zum Löschen:", df["id"] if "id" in df else [])
    if st.button("Löschen") and to_delete:
        for _id in to_delete:
            supabase.table("reference_samples").delete().eq("id", _id).execute()
        st.success("Einträge gelöscht. Bitte Seite neu laden.")

    # CSV Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Datenbank als CSV herunterladen", csv, "reference_samples.csv")

    # CSV Upload
    uploaded_file = st.file_uploader("CSV-Datei hochladen, um die Datenbank zu ergänzen:", type=["csv"])
    if uploaded_file:
        new_df = pd.read_csv(uploaded_file)
        for _, row in new_df.iterrows():
            supabase.table("reference_samples").insert(row.to_dict()).execute()
        st.success("CSV-Daten wurden ergänzt. Bitte Seite neu laden.")