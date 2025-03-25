
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from gotrue.errors import AuthApiError
import io

# Supabase-Konfiguration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔐 Session bei App-Start setzen, falls vorhanden (für RLS)
if "session" in st.session_state:
    supabase.auth.set_session(
        access_token=st.session_state.session.access_token,
        refresh_token=st.session_state.session.refresh_token
    )

st.set_page_config(page_title="Reference Sample Manager", layout="wide")
st.title("📄 Reference Sample Manager")

# Login
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

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Manual Input", "📋 View & Delete", "⬆️ Upload CSV", "⬇️ Download CSV"])

    with tab1:
        st.subheader("📝 Enter a New Reference Sample Manually")
        with st.form("sample_form"):
            lot_number = st.text_input("LOT Number *")
            signal_count = st.number_input("Signal Count *", min_value=0.0)
            true_marker_percent = st.number_input("True % of Marked Fiber *", min_value=0.0)
            ash_color = st.color_picker("Ash Color *")

            percent_natural = st.number_input("Natural Fibers (%)", min_value=0.0)
            percent_black = st.number_input("Black Fibers (%)", min_value=0.0)
            percent_white = st.number_input("White Fibers (%)", min_value=0.0)
            percent_denim = st.number_input("Denim Fibers (%)", min_value=0.0)

            cotton = st.number_input("Cotton (%)", min_value=0.0)
            mmcf = st.number_input("MMCF (%)", min_value=0.0)
            pet = st.number_input("PET (%)", min_value=0.0)
            pa = st.number_input("PA (%)", min_value=0.0)
            acrylic = st.number_input("Acrylic (%)", min_value=0.0)
            recycled_cotton = st.number_input("Recycled Cotton (%)", min_value=0.0)

            mastermix_loading = st.number_input("Mastermix Loading (%)", min_value=0.0)
            enrichment = st.number_input("Enrichment (%)", min_value=0.0)
            furnace_temp = st.number_input("Furnace Temperature (°C)", min_value=0.0)
            furnace_time = st.number_input("Furnace Holding Time (hrs)", min_value=0.0)

            scanner_setting = st.text_input("Scanner Setting")

            submitted = st.form_submit_button("Submit Sample")

            if submitted:
                required = all([lot_number, signal_count, true_marker_percent, ash_color])
                if not required:
                    st.warning("Please fill in all required fields.")
                else:
                    try:
                        data = {
                            "lot_number": lot_number,
                            "percent_natural": int(percent_natural),
                            "percent_black": int(percent_black),
                            "percent_white": int(percent_white),
                            "percent_denim": int(percent_denim),
                            "cotton": int(cotton),
                            "mmcf": int(mmcf),
                            "pet": int(pet),
                            "pa": int(pa),
                            "acrylic": int(acrylic),
                            "recycled_cotton": int(recycled_cotton),
                            "mastermix_loading": float(mastermix_loading),
                            "enrichment": float(enrichment),
                            "ash_color": ash_color,
                            "signal_count": float(signal_count),
                            "furnace_temp": float(furnace_temp),
                            "furnace_time": float(furnace_time),
                            "scanner_setting": scanner_setting,
                            "true_marker_percent": float(true_marker_percent),
                            "submitted_by": user_email
                        }

                        res = supabase.table("reference_samples").insert(data).execute()
                        if res.data:
                            st.success("✅ Sample successfully submitted!")
                            st.rerun()
                        else:
                            st.error("⚠️ Insert failed – check your data.")
                    except Exception as e:
                        st.error("Insert error:")
                        st.exception(e)

    with tab2:
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
                    try:
                        delete_res = supabase.table("reference_samples").delete().eq("lot_number", selected_row).execute()
                        if delete_res.data:
                            st.success(f"Deleted LOT: {selected_row}")
                            st.rerun()
                        else:
                            st.error("Delete failed. Check permissions or data.")
                    except Exception as e:
                        st.error("Delete error:")
                        st.exception(e)
            else:
                st.info("You have no entries to delete.")
        else:
            st.info("No data available.")

    with tab3:
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

    with tab4:
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
    st.info("Please log in to manage, enter, or view data.")
