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

@st.cache_data(ttl=300, show_spinner="Loading data from Supabase...")
def load_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    r = requests.get(SUPABASE_API + "?select=*", headers=headers)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    else:
        st.error("❌ Failed to fetch data from Supabase.")
        return pd.DataFrame()

def build_fiber_models(df, signal_max_limit=1000):
    fiber_cols = ["percent_white", "percent_black", "percent_denim", "percent_natural"]
    models = {}
    for fiber in fiber_cols:
        subset = df[
            (df[fiber] >= 80) &
            df["signal_count"].notna() &
            df["true_marker_percent"].notna() &
            (df["signal_count"] <= signal_max_limit)
        ]
        if len(subset) >= 3:
            X = subset[["signal_count"]]
            y = subset["true_marker_percent"]
            model = LinearRegression().fit(X, y)
            models[fiber] = {"model": model, "X": X, "y": y}
    return models

def estimate_confidence_interval(model, X, y, new_x):
    residuals = y - model.predict(X)
    rmse = np.sqrt(np.mean(residuals**2))
    prediction = model.predict(np.array([[new_x]]))[0]
    prediction = np.clip(prediction, y.min(), y.max())
    lower = prediction - rmse
    upper = prediction + rmse
    return prediction, lower, upper, rmse

# UI
st.title("📊 IntegriTEX – Marker Fiber Estimation")

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
reload = st.button("🔄 Reload data from Supabase")

if reload:
    load_data.clear()
    st.info("✅ Cache cleared – fresh data will be loaded.")

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

    if total != 100:
        st.warning("⚠️ The sum of fiber percentages must equal 100%.")
    else:
        df = load_data()
        if df.empty:
            st.stop()

        ref_match = df[
            (df["signal_count"] == signal) &
            (df["percent_white"] == white) &
            (df["percent_black"] == black) &
            (df["percent_denim"] == denim) &
            (df["percent_natural"] == natural)
        ]
        if not ref_match.empty:
            known_value = ref_match.iloc[0]["true_marker_percent"]
            st.info(f"📌 Known reference found: **{known_value:.2f}%** marker fiber content.")

        max_plot_signal = df[df["signal_count"] <= 1000]["signal_count"].max()
        models = build_fiber_models(df, signal_max_limit=1000)

        if not models:
            st.error("❌ No models could be built.")
            st.stop()

        prediction_total = 0.0
        detailed_rows = []

        for fiber, weight in weights.items():
            entry = models.get(fiber)
            if entry and weight > 0:
                model = entry["model"]
                X = entry["X"]
                y = entry["y"]
                pred, lower, upper, rmse = estimate_confidence_interval(model, X, y, signal)
                prediction_total += weight * pred

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

        plot_df = df[
            df["signal_count"].notna() &
            df["true_marker_percent"].notna() &
            (df["signal_count"] <= 1000)
        ]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_title("Signal vs. Marker – with Regression Lines")
        ax.scatter(
            plot_df["signal_count"],
            plot_df["true_marker_percent"],
            alpha=0.3,
            label="Reference Data"
        )

        x_range = np.linspace(0, max_plot_signal * 1.1, 100)
        ax.set_xlim(0, max_plot_signal * 1.1)
        ax.set_ylim(0, 120)

        for fiber, entry in models.items():
            model = entry["model"]
            y_line = model.predict(x_range.reshape(-1, 1))
            y_line = np.clip(y_line, entry["y"].min(), entry["y"].max())
            ax.plot(x_range, y_line, label=fiber.replace("percent_", "").capitalize())

        ax.scatter(signal, prediction_total, color="red", label="Your Input", zorder=10, s=80)

        ax.set_xlabel("Signal Count")
        ax.set_ylabel("Marker Fiber Content (%)")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
