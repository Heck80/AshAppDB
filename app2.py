import streamlit as st

import pandas as pd

import requests

import numpy as np

import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression

from sklearn.preprocessing import PolynomialFeatures

from sklearn.pipeline import make_pipeline
 
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
 
def determine_dominant_fiber(row):

    """Determine which fiber type has the highest percentage in a sample"""

    fibers = {

        'percent_white': row['percent_white'],

        'percent_black': row['percent_black'],

        'percent_denim': row['percent_denim'],

        'percent_natural': row['percent_natural']

    }

    return max(fibers.items(), key=lambda x: x[1])[0]
 
def build_fiber_models(df, signal_max_limit=1000):

    """Build predictive models for each fiber type"""

    fiber_cols = ["percent_white", "percent_black", "percent_denim", "percent_natural"]

    models = {}

    for fiber in fiber_cols:

        # Get samples where this fiber is dominant (>=50%)

        subset = df[

            (df[fiber] >= 50) &

            df["signal_count"].notna() &

            df["true_marker_percent"].notna() &

            (df["signal_count"] <= signal_max_limit)

        ]

        if len(subset) >= 3:

            # Prepare features: signal_count and fiber percentages

            X = subset[["signal_count", "percent_white", "percent_black", "percent_denim", "percent_natural"]]

            y = subset["true_marker_percent"]

            # Create polynomial regression model (degree=2 for curvature)

            model = make_pipeline(

                PolynomialFeatures(degree=2),

                LinearRegression()

            )

            model.fit(X, y)

            models[fiber] = {

                "model": model,

                "X": X,

                "y": y,

                "min_signal": X["signal_count"].min(),

                "max_signal": X["signal_count"].max()

            }

    return models
 
def predict_marker_content(models, signal, fiber_percentages):

    """Predict marker content using all applicable models"""

    predictions = []

    confidences = []

    # Prepare input features

    input_features = np.array([[

        signal,

        fiber_percentages["percent_white"],

        fiber_percentages["percent_black"],

        fiber_percentages["percent_denim"],

        fiber_percentages["percent_natural"]

    ]])

    for fiber, model_data in models.items():

        if fiber_percentages[fiber] > 0:  # Only use models for present fibers

            model = model_data["model"]

            # Only predict if signal is within model's trained range

            if model_data["min_signal"] <= signal <= model_data["max_signal"]:

                pred = model.predict(input_features)[0]

                residuals = model_data["y"] - model.predict(model_data["X"])

                rmse = np.sqrt(np.mean(residuals**2))

                predictions.append(pred)

                confidences.append(rmse)

    if not predictions:

        return None, None

    # Weighted average prediction based on fiber percentages

    weights = np.array([fiber_percentages[fiber] for fiber in models.keys() 

                       if fiber_percentages[fiber] > 0])

    weights = weights / weights.sum()

    weighted_pred = np.sum(np.array(predictions) * weights)

    weighted_rmse = np.sum(np.array(confidences) * weights)

    return np.clip(weighted_pred, 0, 100), weighted_rmse
 
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
 
    fiber_percentages = {

        "percent_white": white,

        "percent_black": black,

        "percent_denim": denim,

        "percent_natural": natural

    }
 
    if total != 100:

        st.warning("⚠️ The sum of fiber percentages must equal 100%.")

    else:

        df = load_data()

        if df.empty:

            st.stop()
 
        # Add dominant fiber type to dataframe for coloring points

        df['dominant_fiber'] = df.apply(determine_dominant_fiber, axis=1)

        models = build_fiber_models(df, signal_max_limit=1000)
 
        if not models:

            st.error("❌ No models could be built.")

            st.stop()
 
        # Get prediction

        prediction, confidence = predict_marker_content(models, signal, fiber_percentages)

        if prediction is None:

            st.error("❌ No valid prediction could be made (signal outside model range).")

            st.stop()
 
        # Prepare detailed results

        detailed_rows = []

        for fiber in fiber_percentages:

            if fiber_percentages[fiber] > 0:

                detailed_rows.append({

                    "Fiber": fiber.replace("percent_", "").capitalize(),

                    "Percentage": f"{fiber_percentages[fiber]:.0f}%",

                    "Model Applicable": "Yes" if fiber in models else "No"

                })
 
        st.subheader("📈 Prediction Result")

        st.success(f"Estimated Marker Fiber Content: **{prediction:.2f}%**")

        st.info(f"Prediction Confidence Interval: ±{confidence:.2f}%")

        st.subheader("🧾 Model Information")

        st.table(pd.DataFrame(detailed_rows))
 
        # Visualization

        st.subheader("📉 Visualization")
 
        plot_df = df[

            df["signal_count"].notna() &

            df["true_marker_percent"].notna() &

            (df["signal_count"] <= 1000)

        ]
 
        # Create color mapping for fibers

        fiber_colors = {

            "percent_white": "#1f77b4",  # Blue

            "percent_black": "#000000",   # Black

            "percent_denim": "#2ca02c",   # Green

            "percent_natural": "#ff7f0e"   # Orange

        }
 
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.set_title("Marker Fiber Content vs. Signal Count", pad=20)

        # Plot points with colors matching their dominant fiber

        for fiber, color in fiber_colors.items():

            fiber_data = plot_df[plot_df['dominant_fiber'] == fiber]

            if not fiber_data.empty:

                ax.scatter(

                    fiber_data["true_marker_percent"],

                    fiber_data["signal_count"],

                    alpha=0.6,

                    color=color,

                    label=fiber.replace("percent_", "").capitalize() + " samples",

                    s=50,

                    edgecolor='white',

                    linewidth=0.5

                )
 
        # Plot prediction point

        ax.scatter(

            prediction,

            signal,

            color="red",

            marker="*",

            s=300,

            edgecolor='black',

            linewidth=1,

            label="Your Prediction",

            zorder=10

        )
 
        # Add confidence interval

        ax.fill_betweenx(

            [signal * 0.9, signal * 1.1],

            prediction - confidence,

            prediction + confidence,

            color="red",

            alpha=0.2,

            label="Confidence Interval"

        )
 
        ax.set_xlabel("Marker Fiber Content (%)", labelpad=10)

        ax.set_ylabel("Signal Count (counts)", labelpad=10)

        ax.grid(True, alpha=0.3)

        # Customize legend

        handles, labels = ax.get_legend_handles_labels()

        ax.legend(

            handles,

            labels,

            bbox_to_anchor=(1.05, 1),

            loc='upper left',

            frameon=True,

            framealpha=0.8

        )
 
        plt.tight_layout()

        st.pyplot(fig)
 
        # Model equations information

        st.subheader("🧮 Model Equations")

        st.markdown("""

        The predictive models use polynomial regression (degree=2) with the form:

        ```

        Marker% = a·signal² + b·signal + c·white% + d·black% + e·denim% + f·natural% + g

        ```

        Where coefficients (a-g) are learned from the reference data for each fiber type.

        """)
 
