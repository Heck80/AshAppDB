import streamlit as st
import pandas as pd
import requests
from io import StringIO
from gotrue import SyncGoTrueClient
from gotrue.errors import AuthApiError

st.set_page_config(page_title="IntegriTEX – Datenbank", layout="centered")

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SUPABASE_API = f"{SUPABASE_URL}/rest/v1/reference_samples"

auth_client = SyncGoTrueClient(
    url=f"{SUPABASE_URL}/auth/v1",
    headers={"apikey": SUPABASE_KEY}
)

if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

mode = st.sidebar.radio("🔐 Modus:", ["Login", "Registrieren"])
email = st.sidebar.text_input("E-Mail")
password = st.sidebar.text_input("Passwort", type="password")

if mode == "Login":
    if st.sidebar.button("Login"):
        try:
            user = auth_client.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = user
            st.session_state.token = user.session.access_token
            st.success("✅ Login erfolgreich!")
            st.rerun()
        except AuthApiError:
            st.error("❌ Login fehlgeschlagen.")

elif mode == "Registrieren":
    if st.sidebar.button("Registrieren"):
        try:
            reg = auth_client.sign_up({"email": email, "password": password})
            if reg.user:
                st.success("✅ Registrierung erfolgreich. Bitte jetzt einloggen.")
        except Exception as e:
            st.error(f"Fehler: {e}")

# Wenn eingeloggt
if st.session_state.user and st.session_state.token:
    user_email = st.session_state.user.user.email
    token = st.session_state.token
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    st.title("📥 Neue Referenzdaten erfassen")
    with st.form("input_form"):
        st.markdown("## 🧶 Fasermischung & Farberkennung")
        st.markdown('<hr style="border:1px solid #bbb">', unsafe_allow_html=True)

        lot_number = st.text_input("✅ LOT-Nummer")
        true_marker_percent = st.number_input("✅ % Marker Fiber in Sample", 0.0, 100.0, 0.0)

        col1, col2 = st.columns(2)
        with col1:
            percent_natural = st.number_input("✅ Natural Fiber (%)", 0.0, 100.0, 0.0)
            percent_black = st.number_input("✅ Black Fiber (%)", 0.0, 100.0, 0.0)
            mastermix_loading = st.number_input("✅ Mastermix (%)", 0.0, 1.0, 0.1)
        with col2:
            percent_white = st.number_input("✅ White Fiber (%)", 0.0, 100.0, 0.0)
            percent_denim = st.number_input("✅ Denim Fiber (%)", 0.0, 100.0, 0.0)
            enrichment = st.number_input("✅ Enrichment (%)", 0.0, 100.0, 4.0)

        ash_color = st.color_picker("✅ Farbcode (HEX oder RGB)", "#D3D3D3")
        signal_count = st.number_input("✅ Emission Count", 0, 999999)

        st.markdown("## 🧪 Material Composition")
        st.markdown('<hr style="border:1px solid #bbb">', unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            cotton = st.number_input("✅ Cotton (%)", 0.0, 100.0, 0.0)
            mmcf = st.number_input("✅ MMCF (%)", 0.0, 100.0, 0.0)
            pet = st.number_input("✅ PET (%)", 0.0, 100.0, 0.0)
        with col4:
            pa = st.number_input("✅ PA (%)", 0.0, 100.0, 0.0)
            acrylic = st.number_input("✅ Acrylic (%)", 0.0, 100.0, 0.0)
            recycled_cotton = st.number_input("✅ Recycled Cotton (%)", 0.0, 100.0, 0.0)

        st.markdown("## ⚙️ Settings")
        st.markdown('<hr style="border:1px solid #bbb">', unsafe_allow_html=True)

        col5, col6 = st.columns(2)
        with col5:
            furnace_temp = st.number_input("✅ Temperatur (°C)", 0, 1000)
        with col6:
            furnace_time = st.number_input("✅ Brenndauer (min)", 0, 500)

        scanner_setting = st.text_input("✅ Scanner-Einstellung")

        submitted = st.form_submit_button("🚀 Submit Data")
        if submitted:
            payload = {
                "lot_number": lot_number,
                "true_marker_percent": true_marker_percent,
                "percent_natural": percent_natural,
                "percent_black": percent_black,
                "percent_white": percent_white,
                "percent_denim": percent_denim,
                "mastermix_loading": mastermix_loading,
                "enrichment": enrichment,
                "ash_color": ash_color,
                "signal_count": signal_count,
                "cotton": cotton,
                "mmcf": mmcf,
                "pet": pet,
                "pa": pa,
                "acrylic": acrylic,
                "recycled_cotton": recycled_cotton,
                "furnace_temp": furnace_temp,
                "furnace_time": furnace_time,
                "scanner_setting": scanner_setting,
                "submitted_by": user_email
            }
            r = requests.post(SUPABASE_API, headers={**headers, "Prefer": "return=minimal"}, json=payload)
            if r.status_code in [201, 204]:
                st.success("✅ Datensatz gespeichert!")
            else:
                st.error(f"❌ Fehler: {r.status_code} – {r.text}")

    st.divider()
    st.header("📋 Deine gespeicherten Datensätze")

    r = requests.get(f"{SUPABASE_API}?submitted_by=eq.{user_email}", headers=headers)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        if not df.empty:
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Daten als CSV exportieren", csv, "reference_data.csv", "text/csv")

            delete_ids = st.multiselect("🗑️ Einträge löschen (Mehrfachauswahl):", df["id"].tolist())
            if st.button("Lösche ausgewählte"):
                for entry_id in delete_ids:
                    requests.delete(f"{SUPABASE_API}?id=eq.{entry_id}", headers=headers)
                st.success("✅ Gelöscht. Bitte Seite neu laden.")
        else:
            st.info("Noch keine eigenen Datensätze gespeichert.")

    uploaded_file = st.file_uploader("📤 CSV-Datei importieren (inkl. Spalten)", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        data["submitted_by"] = user_email
        import_json = data.to_dict(orient="records")
        r = requests.post(SUPABASE_API, headers={**headers, "Prefer": "resolution=merge-duplicates"}, json=import_json)
        if r.status_code in [201, 204]:
            st.success("✅ CSV erfolgreich importiert!")
        else:
            st.error(f"Fehler beim Importieren: {r.status_code} – {r.text}")
