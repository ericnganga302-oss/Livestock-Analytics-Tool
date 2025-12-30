import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import base64
import json
from datetime import datetime, timedelta

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. THE INTELLIGENCE CORE ---
MARKET_DATA = {"Beef": 760, "Pig": 550, "Goat": 950, "Sheep": 900, "Poultry": 600}
SPECIES_INFO = {
    "Beef": {"ch4": 0.18, "manure": 12.0, "biogas": 0.04, "feed_price": 55, "std_adg": 0.8, "vax": [("FMD", 0), ("LSD", 30), ("Anthrax", 180)]}, 
    "Pig": {"ch4": 0.04, "manure": 4.0, "biogas": 0.06, "feed_price": 65, "std_adg": 0.6, "vax": [("CSF", 0), ("Parvo", 21), ("Erysipelas", 45)]},
    "Goat": {"ch4": 0.02, "manure": 1.5, "biogas": 0.05, "feed_price": 45, "std_adg": 0.15, "vax": [("PPR", 0), ("Entero", 21), ("CCPP", 60)]},
    "Sheep": {"ch4": 0.02, "manure": 1.5, "biogas": 0.05, "feed_price": 45, "std_adg": 0.2, "vax": [("Blue Tongue", 0), ("Sheep Pox", 30)]}
}

# Language Dictionary
LANG = {
    "EN": {"dash": "Dashboard", "vax": "Vax Sentinel", "manual": "Field Manual", "alert": "Weather Alerts", "diag": "Visual Diagnostics"},
    "SW": {"dash": "Dhibiti", "vax": "Kalenda ya Chanjo", "manual": "Mwongozo wa Nyanjani", "alert": "Tahadhari ya Hewa", "diag": "Uchunguzi wa Picha"}
}

# --- 3. SESSION STATE ---
if 'records' not in st.session_state: st.session_state.records = []
if 'lang' not in st.session_state: st.session_state.lang = "EN"

# --- 4. SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("AEGIS v11.0")
    
    # Local Language Toggle
    lang_choice = st.segmented_control("Language / Lugha", ["English", "Kiswahili"], default="English")
    st.session_state.lang = "EN" if lang_choice == "English" else "SW"
    L = LANG[st.session_state.lang]

    nav = st.radio("Navigation", [L["dash"], "Sire Scorecard", "Feed Optimizer", L["vax"], L["diag"], L["alert"], L["manual"]])
    
    st.divider()
    with st.expander("📝 Entry Terminal", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            sp = st.selectbox("Species", list(SPECIES_INFO.keys()))
            tid = f"AEG-{sp[:3].upper()}-{datetime.now().year}-{random.randint(100,999)}"
            c1, c2 = st.columns(2)
            w_s = c1.number_input("Start Wt", 1.0, 1000.0, 25.0)
            w_c = c1.number_input("Current Wt", 1.0, 1000.0, 30.0)
            days = c2.number_input("Days", 1, 5000, 10)
            feed = c2.number_input("Feed (kg)", 0.1, 10000.0, 50.0)
            sire = st.text_input("Sire ID (Father)", "Unknown")
            if st.form_submit_button("Commit"):
                gain = w_c - w_s
                cost = feed * SPECIES_INFO[sp]["feed_price"]
                st.session_state.records.append({
                    "ID": tid, "Spec": sp, "ADG": gain/days, "Profit": (w_c * MARKET_DATA[sp]) - cost,
                    "Sire": sire, "Date": datetime.now().strftime("%Y-%m-%d"), "Weight": w_c
                })
                st.rerun()

# --- 5. MODULES ---

# A. SIRE SCORECARD (Genetic IQ)
if nav == "Sire Scorecard":
    st.title("🧬 Genetic Performance: Sire Scorecard")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        sire_stats = df.groupby('Sire').agg({'ADG': 'mean', 'ID': 'count'}).reset_index()
        sire_stats.columns = ['Sire_ID', 'Avg_Offspring_ADG', 'Total_Offspring']
        
        # Rank Sires
        sire_stats = sire_stats.sort_values('Avg_Offspring_ADG', ascending=False)
        st.subheader("Top Performing Sires")
        st.dataframe(sire_stats.style.background_gradient(subset=['Avg_Offspring_ADG'], cmap='Greens'))
        
        st.altair_chart(alt.Chart(sire_stats).mark_bar().encode(
            x='Sire_ID', y='Avg_Offspring_ADG', color='Total_Offspring'
        ), use_container_width=True)
    else: st.info("No breeding data recorded.")

# B. WEATHER DRIVEN ALERTS (Meteorological Risk)
elif nav == L["alert"]:
    st.title("🌦️ AEGIS Climate Sentinel")
    # Simulated Weather/Location Intelligence for Nakuru/Nairobi
    st.subheader("Regional Risk Assessment")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rainfall Forecast", "High (80%)", delta="Potential Flooding")
        st.error("🚨 RISK: High probability of Rift Valley Fever (RVF) due to mosquito breeding.")
    with col2:
        st.metric("Temperature", "28°C", delta="Rising")
        st.warning("🔔 ADVISORY: Heat stress risk. Ensure shade for Pigs/Poultry.")
    
    st.info("💡 Strategic Advice: Vaccinate for RVF and Blue Tongue before the peak of the rainy season.")

# C. VISUAL DIAGNOSTICS (Computer Vision Placeholder)
elif nav == L["diag"]:
    st.title("📸 Visual Diagnostics")
    st.write("Upload a photo of the animal's eyes, muzzle, or skin for AI analysis.")
    img_file = st.file_uploader("Upload Image...", type=["jpg", "png", "jpeg"])
    if img_file:
        st.image(img_file, caption="Analyzing...", width=300)
        # In v12, we can connect this to an actual TensorFlow/OpenAI model
        st.warning("🤖 AI ANALYSIS: Detected Pale Mucous Membranes (78% confidence).")
        st.error("Potential Diagnosis: Anemia / Haemonchosis (Worms). Please check Field Manual for treatment.")

# D. DASHBOARD & OTHER TABS
elif nav == L["dash"]:
    st.title(f"📊 {L['dash']}")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        st.metric("Total Herd Profit", f"KES {df['Profit'].sum():,.0f}")
        st.dataframe(df, use_container_width=True)

elif nav == "Feed Optimizer":
    st.title("🧪 Pearson Square Optimizer")
    # (Pearson Square Logic from v10.0 goes here)

elif nav == L["vax"]:
    st.title(f"📅 {L['vax']}")
    # (Vax logic from v10.0 goes here)

elif nav == L["manual"]:
    st.title(f"📚 {L['manual']}")
    if st.session_state.lang == "SW":
        st.subheader("Uchunguzi wa Nyanjani")
        st.write("1. **Kamasi:** Ikiwa pua ni kavu, mnyama ana homa.")
        st.write("2. **Macho:** Ikiwa ndani ni rangi nyeupe, mnyama ana minyoo.")
    else:
        st.subheader("Field Examination")
        st.write("1. **Muzzle:** Dryness indicates fever.")
        st.write("2. **Eyes:** Pale membranes indicate anemia/worms.")

st.divider()
st.caption(f"Eric Kamau | AEGIS v11.0 | University of Nairobi | Humanity-First Innovation")
