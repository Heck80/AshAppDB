import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="IntegriTEX – Analysis", layout="centered")

SUPABASE_URL = "https://afcpqvesmqvfzbcilffx.supabase.co"
SUPABASE_API = f"{SUPABASE_URL}/rest/v1/reference_samples"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFmY3BxdmVzbXF2ZnpiY2lsZmZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5MjI0MjAsImV4cCI6MjA1ODQ5ODQyMH0.8jJDrlUBcWtYRGyjlvnFvKDf_gn54ozzgD2diGfrFb4"

@st.cache_data
def load_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    r = requests.get(SUPABASE_API + "?select=*", headers=headers)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        st.write("📦 Rohdaten aus Supabase:", df.shape)
        st.dataframe(df.head(10))  # Vorschau für Debug
        # Konvertiere alle Spalten nach Möglichkeit
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    else:
        st.error("❌ Fehler beim Abrufen der Daten")
        return pd.DataFrame()

def build_fiber_models(df):
    signal_col = "signal_count"
    target_col = "true_marker_percent"
    fiber_cols = ["percent_white", "percent_black", "percent_denim", "percent_natural"]
    models = {}
    for fiber in fiber_cols:
        subset = df[(df[fiber] >= 80) & df[signal_col].notna() & df[target_col].notna()]
        st.write(f"📊 Datenpunkte für Modell '{fiber}':", len(subset))
        if len(subset) >= 3:
            X = subset[[signal_col]]
            y = subset[target_col]
            model = LinearRegression().fit(X, y)
            models[fiber] = model
    return models

def predict_weighted(signal_value, weights, models):
    prediction = 0.0
    used_fibers = []
    for fiber, weight in weights.items():
        model = models.get(fiber)
        if model and weight > 0:
            pred = model.predict(np.array([[signal_value]]))[0]
            prediction += weight * pred
            used_fibers.append(fiber)
    return prediction, used_fibers

# App UI
st.title("📊 IntegriTEX – Marker Fiber Estimation (Debug-Modus)")

st.subheader("🔍 Eingabe")
signal = st.number_input("Signal (count value)", min_value=0, value=1000)

col1, col2 = st.columns(2)
with col1:
    white = st.number_input("White (%)", 0, 100, step=1)
    black = st.number_input("Black (%)", 0, 100, step=1)
with col2:
    denim = st.number_input("Denim (%)", 0, 100, step=1)
    natural = st.number_input("Natural (%)", 0, 100, step=1)

submit = st.button("🔍 Analyse starten")

total = white + black + denim + natural
if submit:
    st.subheader("🧾 Eingabeübersicht")
    st.write("Signal:", signal)
    st.write("Gesamte Faserblend:", total, "%")
    weights = {
        "percent_white": white / 100,
        "percent_black": black / 100,
        "percent_denim": denim / 100,
        "percent_natural": natural / 100
    }
    st.write("Gewichtete Eingaben:", weights)

    if total != 100:
        st.warning("⚠️ Bitte stelle sicher, dass die Summe der Fasern genau 100 % ergibt.")
    else:
        df = load_data()
        if df.empty:
            st.error("❌ Keine Daten geladen.")
            st.stop()

        models = build_fiber_models(df)
        if not models:
            st.error("❌ Keine Modelle konnten erstellt werden.")
            st.stop()

        st.success(f"✅ Modelle erfolgreich erstellt für: {', '.join(models.keys())}")

        prediction, used_fibers = predict_weighted(signal, weights, models)

        if not used_fibers:
            st.warning("⚠️ Es wurden keine gültigen Modelle für deine Eingabe gefunden.")
            st.stop()

        st.success(f"📈 Geschätzter Marker-Faseranteil: **{prediction:.2f}%**")
        st.caption(f"(Basierend auf: {', '.join(used_fibers)})")

        # Plot
        st.subheader("📉 Visualisierung")
        df_plot = df[["signal_count", "true_marker_percent"]].dropna()
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(df_plot["signal_count"], df_plot["true_marker_percent"], alpha=0.4, label="Referenzdaten")
        ax.scatter(signal, prediction, color="red", label="Dein Wert", zorder=10)
        ax.set_xlabel("Signal Count")
        ax.set_ylabel("Marker Fiber Content (%)")
        ax.set_title("Signal vs. Marker")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
