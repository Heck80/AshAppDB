import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
 
# [Previous code remains the same until the build_fiber_models function]
 
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
 
# [Previous UI code remains the same until the prediction section]
 
if submit:
    # [Previous input validation code remains the same]
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
 
        # Prepare fiber percentages dictionary
        fiber_percentages = {
            "percent_white": white,
            "percent_black": black,
            "percent_denim": denim,
            "percent_natural": natural
        }
 
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
 
        # [Rest of the visualization code remains the same]
