    # --- Abschnitt: Fasermischung & Farberkennung ---
    st.markdown("## 🧶 Fasermischung & Farberkennung")
    st.markdown('<hr style="border:1px solid #bbb">', unsafe_allow_html=True)

    lot_number = st.text_input("✅ LOT-Nummer")
    true_marker_percent = st.number_input("✅ % Marker Fiber in Sample", 0.0, 100.0, 0.0)

    col1, col2 = st.columns(2)
    with col1:
        percent_natural = st.number_input("✅ Natural Fiber (%)", 0.0, 100.0, 0.0)
        percent_black = st.number_input("✅ Black Fiber (%)", 0.0, 100.0, 0.0)
        mastermix_loading = st.number_input("✅ Mastermix (%)", 0.0, 1.0, 0.1)
    with col2:
        percent_white = st.number_input("✅ White Fiber (%)", 0.0, 100.0, 0.0)
        percent_denim = st.number_input("✅ Denim Fiber (%)", 0.0, 100.0, 0.0)
        enrichment = st.number_input("✅ Enrichment (%)", 0.0, 100.0, 4.0)

    ash_color = st.color_picker("✅ Farbcode (HEX oder RGB)", "#D3D3D3")
    signal_count = st.number_input("✅ Emission Count", 0, 999999)

    # --- Abschnitt: Material Composition ---
    st.markdown("## 🧪 Material Composition")
    st.markdown('<hr style="border:1px solid #bbb">', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        cotton = st.number_input("✅ Cotton (%)", 0.0, 100.0, 0.0)
        mmcf = st.number_input("✅ MMCF (%)", 0.0, 100.0, 0.0)
        pet = st.number_input("✅ PET (%)", 0.0, 100.0, 0.0)
    with col4:
        pa = st.number_input("✅ PA (%)", 0.0, 100.0, 0.0)
        acrylic = st.number_input("✅ Acrylic (%)", 0.0, 100.0, 0.0)
        recycled_cotton = st.number_input("✅ Recycled Cotton (%)", 0.0, 100.0, 0.0)

    # --- Abschnitt: Settings ---
    st.markdown("## ⚙️ Settings")
    st.markdown('<hr style="border:1px solid #bbb">', unsafe_allow_html=True)

    col5, col6 = st.columns(2)
    with col5:
        furnace_temp = st.number_input("✅ Temperatur (°C)", 0, 1000)
    with col6:
        furnace_time = st.number_input("✅ Brenndauer (min)", 0, 500)

    scanner_setting = st.text_input("✅ Scanner-Einstellung")

    submitted = st.form_submit_button("🚀 Submit Data")
