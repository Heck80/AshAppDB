import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="IntegriTEX – Analysis", layout="centered")

SUPABASE_URL = "https://afcpqvesmqvfzbcilffx.supabase.co"
SUPABASE_API = f"{SUPABASE_URL}/rest/v1/reference_samples"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFmY3BxdmVzbXF2ZnpiY2lsZmZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5MjI0MjAsImV4cCI6MjA1ODQ5ODQyMH0.8jJDrlUBcWtYRGyjlvnFvKDf_gn54ozzgD2diGfrFb4"  # <-- Hier vollständigen anon-API-Key einsetzen

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
        # ✅ Verbesserte Fehlerausgabe
        st.error(f"❌ Supabase request failed. Status code: {r.status_code}")
        st.text(f"Response text: {r.text}")
        return pd.DataFrame()

def determine_dominant_fiber(row):
    fibers = {
        'percent_white': row['percent_white'],
        'percent_black': row['percent_black'],
        'percent_denim': row['percent_denim'],
        'percent_natural': row['percent_natural']
    }
    return max(fibers.items(), key=lambda x: x[1])[0]

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
            X = subset[["true_marker_percent"]]
            y = subset["signal_count"]
            model = LinearRegression().fit(X, y)
            models[fiber] = {"model": model, "X": X, "y": y}
    return models

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

        df['dominant_fiber'] = df.apply(determine_dominant_fiber, axis=1)

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

                # Rückrechnung des Markeranteils
                a_i = model.coef_[0]
                b_i = model.intercept_

                marker_percent = (signal - b_i) / a_i
                marker_percent = np.clip(marker_percent, 0, 100)

                prediction_total += weight * marker_percent

                residuals = y - model.predict(X)
                rmse = np.sqrt(np.mean(residuals**2))

                detailed_rows.append({
                    "Fiber": fiber.replace("percent_", "").capitalize(),
                    "Weight": f"{weight*100:.0f} %",
                    "Estimated Marker %": f"{marker_percent:.2f} %",
                    "Regression (a)": f"{a_i:.2f}",
                    "Confidence (±)": f"{rmse:.1f} counts"
                })

        prediction_total = np.clip(prediction_total, 0, 100)
        st.subheader("📈 Prediction Result")
        st.success(f"Estimated Marker Fiber Content: **{prediction_total:.2f}%**")
        st.table(pd.DataFrame(detailed_rows))

        # 📉 Plot
        st.subheader("📉 Visualization")

        plot_df = df[
            df["signal_count"].notna() &
            df["true_marker_percent"].notna() &
            (df["signal_count"] <= 1000)
        ]

        fiber_colors = {
            "percent_white": "blue",
            "percent_black": "black",
            "percent_denim": "green",
            "percent_natural": "orange"
        }

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title("Marker Fiber Content vs. Signal Count")

        for fiber, color in fiber_colors.items():
            fiber_data = plot_df[plot_df['dominant_fiber'] == fiber]
            if not fiber_data.empty:
                ax.scatter(
                    fiber_data["true_marker_percent"],
                    fiber_data["signal_count"],
                    alpha=0.5,
                    color=color,
                    label=fiber.replace("percent_", "").capitalize() + " samples",
                    s=40
                )

        x_range = np.linspace(0, 100, 100)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, max_plot_signal * 1.1)

        for fiber, entry in models.items():
            model = entry["model"]
            y_line = model.predict(x_range.reshape(-1, 1))
            y_line = np.clip(y_line, entry["y"].min(), entry["y"].max())
            ax.plot(
                x_range, 
                y_line, 
                color=fiber_colors[fiber],
                linestyle='--',
                linewidth=2,
                label=fiber.replace("percent_", "").capitalize() + " regression"
            )

        ax.scatter(
            prediction_total, 
            signal, 
            color="red", 
            marker="*",  
            s=200,      
            edgecolor='black',
            linewidth=1,
            label="Your Input",
            zorder=10
        )

        ax.set_xlabel("Marker Fiber Content (%)")
        ax.set_ylabel("Signal Count (counts)")
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig)
