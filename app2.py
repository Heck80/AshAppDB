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
    r = requests.get(SUPABASE_API, headers=headers)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip("'")
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.dropna(subset=["signal_count", "true_marker_percent"])
    else:
        st.error("❌ Failed to load reference data from Supabase")
        return pd.DataFrame()

def build_fiber_models(df):
    signal_col = "signal_count"
    target_col = "true_marker_percent"
    fiber_cols = ["percent_white", "percent_black", "percent_denim", "percent_natural"]
    models = {}
    for fiber in fiber_cols:
        subset = df[(df[fiber] >= 80)]
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

# UI
st.title("📊 IntegriTEX – Marker Fiber Estimation (Weighted Linear Model)")

with st.expander("ℹ️ Help"):
    st.markdown("""
    Estimate the marker fiber content in a textile sample using a signal count and fiber composition (White, Black, Denim, Natural).
    This version uses a weighted linear regression based on fiber-specific models.
    """)

st.subheader("🔍 Input")
signal = st.number_input("Signal (count value)", min_value=0, value=1000)

col1, col2 = st.columns(2)
with col1:
    white = st.number_input("White (%)", 0, 100, step=1)
    black = st.number_input("Black (%)", 0, 100, step=1)
with col2:
    denim = st.number_input("Denim (%)", 0, 100, step=1)
    natural = st.number_input("Natural (%)", 0, 100, step=1)

submit = st.button("🔍 Run Analysis")

total = white + black + denim + natural
if submit:
    st.subheader("📥 Input Summary")
    st.write("Signal:", signal)
    st.write("Fiber Blend Total:", total, "%")
    weights = {
        "percent_white": white / 100,
        "percent_black": black / 100,
        "percent_denim": denim / 100,
        "percent_natural": natural / 100
    }
    st.write("Weights:", weights)

    if total != 100:
        st.warning(f"⚠️ Fiber blend total is {total}%. Please adjust to 100%.")
    else:
        df = load_data()
        st.write("📦 Loaded reference data:", df.shape)
        if df.empty:
            st.error("❌ Reference data could not be loaded or is empty.")
            st.stop()

        # Optional: Show preview
        with st.expander("🧾 Preview Reference Data"):
            st.dataframe(df.head(10))

        models = build_fiber_models(df)
        if not models:
            st.error("❌ No regression models could be built. Check your reference data (need ≥3 samples with ≥80% fiber).")
            st.stop()

        st.success(f"✅ Built models for: {', '.join(models.keys())}")

        prediction, used_fibers = predict_weighted(signal, weights, models)

        if not used_fibers:
            st.warning("⚠️ None of the selected fiber types have valid models for prediction.")
            st.stop()

        st.success(f"📈 Estimated Marker Fiber Content: **{prediction:.2f}%**")
        st.caption(f"(Based on weighted linear regression using: {', '.join(used_fibers)})")

        st.subheader("🧭 Visualization")
        df_plot = df[["signal_count", "true_marker_percent"]].dropna()
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(df_plot["signal_count"], df_plot["true_marker_percent"], alpha=0.4, label="Reference Data")
        ax.scatter(signal, prediction, color="red", label="Your Input", zorder=10)
        ax.set_xlabel("Signal Count")
        ax.set_ylabel("Marker Fiber Content (%)")
        ax.set_title("Signal vs. Marker Content")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
