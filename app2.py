
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
                df[col] = df[col].astype(str).strip("'")
        numeric_cols = [
            "true_marker_percent", "signal_count", "percent_white", "percent_black",
            "percent_denim", "percent_natural"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.dropna(subset=["signal_count", "percent_white", "percent_black", "percent_denim", "percent_natural"])
    else:
        st.error("Failed to load reference data from Supabase")
        return pd.DataFrame()

def fit_weighted_model(df):
    df = df.copy()
    df = df[df["true_marker_percent"].notna()]
    X = df[["signal_count", "percent_white", "percent_black", "percent_denim", "percent_natural"]]
    y = df["true_marker_percent"]
    model = LinearRegression()
    model.fit(X, y)
    return model

st.title("📊 IntegriTEX – Marker Fiber Estimation")

with st.expander("ℹ️ Help"):
    st.markdown("""
    This tool estimates the marker fiber content in a textile sample based on a measured luminescence signal and fiber composition (White, Black, Denim, Natural). The prediction is based on historical reference data and a weighted regression model.
    """)

st.subheader("🔍 Input")
signal = st.number_input("Signal (count value)", min_value=0, value=1000)
col1, col2 = st.columns(2)
with col1:
    white = st.slider("White (%)", 0, 100, 0)
    black = st.slider("Black (%)", 0, 100, 0)
with col2:
    denim = st.slider("Denim (%)", 0, 100, 0)
    natural = st.slider("Natural (%)", 0, 100, 0)

total = white + black + denim + natural
if total != 100:
    st.warning(f"Fiber blend total is {total}%. Please adjust to 100%.")
else:
    df = load_data()
    if not df.empty:
        model = fit_weighted_model(df)
        X_pred = pd.DataFrame.from_dict({
            "signal_count": [signal],
            "percent_white": [white],
            "percent_black": [black],
            "percent_denim": [denim],
            "percent_natural": [natural]
        })
        prediction = model.predict(X_pred)[0]
        st.success(f"📈 Estimated Marker Fiber Content: **{prediction:.2f}%**")
        st.caption("(Based on a linear model using fiber blend weights)")

        with st.expander("📉 Show model coefficients"):
            coefs = pd.Series(model.coef_, index=X_pred.columns)
            st.write(coefs)

        st.subheader("🧭 Visualization")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(df["signal_count"], df["true_marker_percent"], alpha=0.4, label="Reference Data")
        ax.scatter(signal, prediction, color="red", label="Your Input", zorder=10)
        ax.set_xlabel("Signal Count")
        ax.set_ylabel("Marker Fiber Content (%)")
        ax.set_title("Signal vs. Marker Content")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.stop()
