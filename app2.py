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
        st.write("📦 Raw data from Supabase:", df.shape)
        st.dataframe(df.head(10))
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    else:
        st.error("❌ Failed to fetch data from Supabase.")
        return pd.DataFrame()

def build_fiber_models(df, signal_max_limit=1000):
    signal_col = "signal_count"
    target_col = "true_marker_percent"
    fiber_cols = ["percent_white", "percent_black", "percent_denim", "percent_natural"]
    models = {}
    for fiber in fiber_cols:
        subset = df[
            (df[fiber] >= 80) &
            df[signal_col].notna() &
            df[target_col].notna() &
            (df[signal_col] <= signal_max_limit)
        ]
        st.write(f"📊 Data points for model '{fiber}':", len(subset))
        if len(subset) >= 3:
            X = subset[[signal_col]]
            y = subset[target_col]
            model = LinearRegression().fit(X, y)
            models[fiber] = model
    return models

def estimate_confidence_interval(model, X, y, new_x):
    residuals = y - model.predict(X)
    rmse = np.sqrt(np.mean(residuals**2))
    prediction = model.predict(np.array([[new_x]]))[0]
    lower = prediction - rmse
    upper = prediction + rmse
    return prediction, lower, upper, rmse

# UI
st.title("📊 IntegriTEX – Marker Fiber Estimation (with Confidence Intervals)")

st.subheader("🔍 Input")
signal = st.number_input("Signal (count value)", min_value=0, value=100)

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
    st.subheader("🧾 Input Summary")
    st.write("Signal:", signal)
    st.write("Total Fiber Blend:", total, "%")

    weights = {
        "percent_white": white / 100,
        "percent_black": black / 100,
        "percent_denim": denim / 100,
        "percent_natural": natural / 100
    }
    st.write("Weights:", weights)

    if total != 100:
        st.warning("⚠️ The sum of fiber percentages must equal 100%.")
    else:
        df = load_data()
        if df.empty:
            st.stop()

        # Use real max signal to limit models and plotting
        max_signal = df["signal_count"].max()
        models = build_fiber_models(df, signal_max_limit=max_signal)
        if not models:
            st.error("❌ No models could be built.")
            st.stop()

        st.success(f"✅ Models available for: {', '.join(models.keys())}")

        prediction_total = 0.0
        total_weight = 0.0
        detailed_rows = []

        for fiber, weight in weights.items():
            model = models.get(fiber)
            if model and weight > 0:
                subset = df[
                    (df[fiber] >= 80) &
                    df["signal_count"].notna() &
                    df["true_marker_percent"].notna()
                ]
                X = subset[["signal_count"]]
                y = subset["true_marker_percent"]
                pred, lower, upper, rmse = estimate_confidence_interval(model, X, y, signal)

                prediction_total += weight * pred
                total_weight += weight

                detailed_rows.append({
                    "Fiber": fiber.replace("percent_", "").capitalize(),
                    "Weight": f"{weight*100:.0f} %",
                    "Prediction": f"{pred:.2f} %",
                    "Confidence ±": f"{rmse:.2f}"
                })

        st.subheader("📈 Prediction Result")
        st.success(f"Estimated Marker Fiber Content: **{prediction_total:.2f}%**")
        st.table(pd.DataFrame(detailed_rows))

        # Plot
        st.subheader("📉 Visualization")

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_title("Signal vs. Marker – with Regression Lines")

        df_plot = df[["signal_count", "true_marker_percent"]].dropna()
        ax.scatter(df_plot["signal_count"], df_plot["true_marker_percent"], alpha=0.3, label="Reference Data")

        x_range = np.linspace(0, max_signal * 1.1, 100)
        ax.set_xlim(0, max_signal * 1.1)
        ax.set_ylim(0, 120)

        for fiber, model in models.items():
            y_line = model.predict(x_range.reshape(-1, 1))
            ax.plot(x_range, y_line, label=fiber.replace("percent_", "").capitalize())

        ax.scatter(signal, prediction_total, color="red", label="Your Input", zorder=10, s=80)
        ax.set_xlabel("Signal Count")
        ax.set_ylabel("Marker Fiber Content (%)")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
