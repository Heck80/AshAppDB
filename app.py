
import streamlit as st
from supabase import create_client, Client
import json
from gotrue.errors import AuthApiError

# Supabase-Konfiguration aus secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="App1 Debug Auth", layout="wide")
st.title("🔐 Debug Auth – Reference Sample Entry")

# Login-Funktion
with st.sidebar:
    st.header("Login / Sign up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    login_mode = st.radio("Action", ["Login", "Sign up"])

    if st.button("Continue"):
        try:
            if login_mode == "Sign up":
                res = supabase.auth.sign_up({"email": email, "password": password})
            else:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})

            if res.user is None:
                st.error("❌ Login failed. Check credentials or confirmation status.")
            else:
                st.session_state.user = res.user
                st.success("✅ Logged in successfully!")

        except AuthApiError as e:
            st.error("❌ Supabase Auth Error:")
            st.exception(e)
        except Exception as e:
            st.error("❌ General Exception:")
            st.exception(e)

if "user" in st.session_state:
    st.success(f"Logged in as: {st.session_state.user.email}")
    st.info("✅ Auth ready – continue with form code...")
else:
    st.info("Please log in or sign up to continue.")
