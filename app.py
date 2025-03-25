
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from gotrue.errors import AuthApiError
import io

# Supabase-Konfiguration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Reference Sample Manager", layout="wide")
st.title("📄 Reference Sample Manager")

# Login mit Session-Übergabe
with st.sidebar:
    st.header("🔐 Login / Sign up")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        action = st.radio("Choose action", ["Login", "Sign up"])
        login_submit = st.form_submit_button("Continue")

        if login_submit:
            if not email or not password:
                st.warning("Please provide both email and password.")
            elif len(password) < 6:
                st.warning("Password must be at least 6 characters.")
            else:
                try:
                    if action == "Sign up":
                        res = supabase.auth.sign_up({"email": email, "password": password})
                    else:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})

                    if res.user:
                        st.session_state.user = res.user
                        st.session_state.session = res.session
                        supabase.auth.set_session(
                            access_token=res.session.access_token,
                            refresh_token=res.session.refresh_token
                        )
                        st.success("Successfully logged in!")
                    else:
                        st.error("Login failed. Please check credentials.")

                except AuthApiError as e:
                    st.error("Authentication error:")
                    st.exception(e)
                except Exception as e:
                    st.error("Unexpected error:")
                    st.exception(e)

if "user" in st.session_state:
    user_email = st.session_state.user.email
    st.success(f"Logged in as: {user_email}")

    tab1, tab2, tab3 = st.tabs(["📋 View & Delete", "⬆️ Upload CSV", "⬇️ Download CSV"])

    with tab1:
        st.subheader("📋 Current Database Entries")
        response = supabase.table("reference_samples").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            st.dataframe(df)

            own_rows = df[df["submitted_by"] == user_email]
            st.markdown("### 🗑️ Delete Your Entries")
            if not own_rows.empty:
                selected_row = st.selectbox("Select LOT to delete", own_rows["lot_number"].tolist())
                if st.button("Delete selected LOT"):
                    delete_res = supabase.table("reference_samples").delete().eq("lot_number", selected_row).execute()
                    if delete_res.data:
                        st.success(f"Deleted LOT: {selected_row}")
                        st.experimental_rerun()
                    else:
                        st.error("Delete failed.")
            else:
                st.info("You have no entries to delete.")
        else:
            st.info("No data available.")

    with tab2:
        st.subheader("⬆️ Upload CSV File")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file:
            try:
                csv_df = pd.read_csv(uploaded_file)
                csv_df["submitted_by"] = user_email
                records = csv_df.to_dict(orient="records")
                insert_res = supabase.table("reference_samples").insert(records).execute()
                if insert_res.data:
                    st.success("CSV data uploaded successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Insert failed. Check your CSV format.")
            except Exception as e:
                st.error("CSV Upload Error:")
                st.exception(e)

    with tab3:
        st.subheader("⬇️ Download Full Dataset")
        if response.data:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name="reference_samples_export.csv",
                mime="text/csv"
            )
else:
    st.info("Please log in to manage or view data.")
