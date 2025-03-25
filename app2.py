
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import re

# --- Supabase Config aus secrets.toml ---
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Analyze Marker Fiber", layout="wide")
st.title("🔍 Marker Fiber Analyzer – App 2")

# --- Load reference data ---
@st.cache_data
def load_data():
    response = supabase.table("reference_samples").select("*").execute()
    df = pd.DataFrame(response.data)
    df = df.dropna(subset=["signal_count", "true_marker_percent", "ash_color", "percent_black", "percent_white"])
    return df

df = load_data()

if df.empty:
    st.warning("No data found in Supabase. Please enter reference samples first.")
    st.stop()

# --- Helper to convert hex color to brightness (approx) ---
def hex_to_luminance(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return 0.299*r + 0.587*g + 0.114*b  # standard luminance formula

df["ash_luminance"] = df["ash_color"].apply(hex_to_luminance)

# --- Define features and target ---
feature_cols = [
    "signal_count", "percent_black", "percent_white", "ash_luminance"
]

# Include optional fields if available
optional_cols = [
    "cotton", "mmcf", "pet", "pa", "acrylic", "recycled_cotton",
    "mastermix_loading", "enrichment", "furnace_temp", "furnace_time"
]

for col in optional_cols:
    if col in df.columns:
        feature_cols.append(col)

X = df[feature_cols].fillna(0)
y = df["true_marker_percent"]

# --- Model Training ---
model_choice = st.selectbox("Choose prediction model", ["Linear Regression", "Random Forest"])
if model_choice == "Linear Regression":
    model = LinearRegression()
else:
    model = RandomForestRegressor(n_estimators=100, random_state=42)

model.fit(X, y)
y_pred = model.predict(X)
mae = mean_absolute_error(y, y_pred)

# --- Input Section for Prediction ---
st.subheader("🔬 Predict Marked Fiber Content")
with st.form("prediction_form"):
    signal = st.number_input("Signal (Count)", min_value=0.0)
    black = st.number_input("Black Fibers (%)", min_value=0.0, max_value=100.0)
    white = st.number_input("White Fibers (%)", min_value=0.0, max_value=100.0)
    ash_color = st.color_picker("Ash Color")

    additional_inputs = {}
    for col in optional_cols:
        if col in df.columns:
            val = st.number_input(f"{col.replace('_',' ').title()} (%)", min_value=0.0, value=0.0)
            additional_inputs[col] = val

    submitted = st.form_submit_button("🔍 Predict")

    if submitted:
        ash_lum = hex_to_luminance(ash_color)
        input_data = {
            "signal_count": signal,
            "percent_black": black,
            "percent_white": white,
            "ash_luminance": ash_lum
        }
        input_data.update(additional_inputs)
        input_df = pd.DataFrame([input_data])[feature_cols]
        prediction = model.predict(input_df)[0]
        st.success(f"📈 Estimated % of Marked Fiber: **{prediction:.3f}%**")
        
        # Optional: Show model performance
        st.caption(f"Model MAE on training data: {mae:.3f}")

# --- Plotting ---
st.subheader("📊 Regression Overview")

fig, ax = plt.subplots()
scatter = ax.scatter(df["signal_count"], y, c=df["ash_luminance"], cmap="gray", label="Reference Samples")
ax.set_xlabel("Signal Count")
ax.set_ylabel("True % Marked Fiber")
ax.set_title("Regression Fit")

# Show line only for Linear Regression
if model_choice == "Linear Regression":
    sorted_idx = np.argsort(df["signal_count"])
    ax.plot(df["signal_count"].iloc[sorted_idx], y_pred[sorted_idx], color="red", label="Fit")
ax.legend()
st.pyplot(fig)
