
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Supabase Test", layout="centered")

st.title("🔍 Supabase Reference Data Test")

SUPABASE_URL = "https://afcpqvesmqvfzbcilffx.supabase.co"
SUPABASE_API = f"{SUPABASE_URL}/rest/v1/reference_samples"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFmY3BxdmVzbXF2ZnpiY2lsZmZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5MjI0MjAsImV4cCI6MjA1ODQ5ODQyMH0.8jJDrlUBcWtYRGyjlvnFvKDf_gn54ozzgD2diGfrFb4"

st.write("Connecting to Supabase...")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

response = requests.get(SUPABASE_API, headers=headers)

if response.status_code == 200:
    try:
        df = pd.DataFrame(response.json())
        if df.empty:
            st.warning("✅ Connection OK – but no data returned from Supabase.")
        else:
            st.success(f"✅ Connection successful! {len(df)} rows loaded.")
            st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"Parsing error: {e}")
else:
    st.error(f"❌ Failed to load data. Status code: {response.status_code}")
    st.code(response.text)
