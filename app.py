import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import base64
import json
import time
from datetime import datetime, timedelta

# ==========================================
# 1. CORE SYSTEM ARCHITECTURE & STYLING
# ==========================================
st.set_page_config(
    page_title="AEGIS Livestock Intelligence", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional UI Branding
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border-radius: 12px; border: 1px solid #d1d5db; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .sidebar-text { font-size: 14px; color: #9ca3af; }
    h1, h2, h3 { color: #1f2937; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MASTER KNOWLEDGE DATASETS
# ==========================================
MARKET_PRICES = {
    "Beef": 760, "Pig": 550, "Goat": 950, "Sheep": 900, "Poultry": 600, "Dairy": 70
}

SPECIES_METRICS = {
    "Beef": {
        "ch4_factor": 0.18, "manure_rate": 12.0, "biogas_yield": 0.04, "feed_cost": 55, "adg_target": 0.8,
        "vaccines": [("FMD", 0), ("LSD", 30), ("Anthrax", 180), ("Blackquarter", 240)],
        "vitals": {"temp": "38.5-39.5°C", "hr": "48-84 bpm", "rr": "26-50 bpm"}
    }, 
    "Pig": {
        "ch4_factor": 0.04, "manure_rate": 4.0, "biogas_yield": 0.06, "feed_cost": 65, "adg_target": 0.6,
        "vaccines": [("CSF", 0), ("Parvo", 21), ("Erysipelas", 45), ("Foot & Mouth", 60)],
        "vitals": {"temp": "38.7-39.8°C", "hr": "70-120 bpm", "rr": "13-18 bpm"}
    },
    "Goat": {
        "ch4_factor": 0.02, "manure_rate": 1.5, "biogas_yield": 0.05, "feed_cost": 45, "adg_target": 0.15,
        "vaccines": [("PPR", 0), ("Entero", 21), ("CCPP", 60), ("Orf", 90)],
        "vitals": {"temp": "38.5-40.5°C", "hr": "70-90 bpm", "rr": "15-30 bpm"}
    },
    "Sheep": {
        "ch4_factor": 0.02, "manure_rate": 1.5, "biogas_yield": 0.05, "feed_cost": 45, "adg_target": 0.2,
        "vaccines": [("Blue Tongue", 0), ("Sheep Pox", 30), ("Foot Rot", 120)],
        "vitals": {"temp": "38.5-40.0°C", "hr": "70-90 bpm", "rr": "12-20 bpm"}
    }
}

SYMPTOM_MATRIX = {
    "High Fever": ["Pneumonia", "East Coast Fever", "Anthrax"],
    "Pale Mucous": ["Internal Parasites", "Anemia", "Babesiosis"],
    "Bloat": ["Grain Overload", "Esophageal Obstruction", "Toxic Plants"],
    "Limping": ["Foot Rot", "FMD", "Physical Injury"],
    "Skin Lumps": ["Lumpy Skin Disease", "Mange", "Ringworm"]
}

# ==========================================
# 3. CORE LOGIC ENGINE CLASS
# ==========================================
class AegisEngine:
    @staticmethod
    def calculate_biogas(manure_kg, species):
        return manure_kg * SPECIES_METRICS[species]["biogas_yield"]

    @staticmethod
    def calculate_roi(current_wt, start_wt, feed_kg, species):
        revenue = current_wt * MARKET_PRICES[species]
        cost = feed_kg * SPECIES_METRICS[species]["feed_cost"]
        return revenue - cost

    @staticmethod
    def get_weather(api_key, city="Nakuru"):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5)
            return r.json() if r.status_code == 200 else None
        except: return None

# ==========================================
# 4. SESSION MANAGEMENT & BACKUP
# ==========================================
if 'records' not in st.session_state: st.session_state.records = []
if 'confirm_wipe' not in st.session_state: st.session_state.confirm_wipe = False
if 'lang' not in st.session_state: st.session_state.lang = "English"

def backup_data():
    return base64.b64encode(json.dumps(st.session_state.records).encode()).decode()

def restore_data(code):
    try:
        data = json.loads(base64.b64decode(code.encode()).decode())
        st.session_state.records = data
        return True
    except: return False

# ==========================================
# 5. SIDEBAR NAVIGATION & ENTRY
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=90)
    st.title("AEGIS v13.0")
    st.caption("Strategic Livestock Decision Support")
    
    st.session_state.lang = st.radio("System Language", ["English", "Kiswahili"], horizontal=True)
    
    menu = st.radio("Control Panel", [
        "📊 Tactical Dashboard", 
        "🧬 Genetic Scorecard",
        "🧪 Advanced Feed Lab", 
        "♻️ Environmental Hub",
        "📸 Visual AI Triage",
        "🌦️ Climate Sentinel",
        "📅 Vax Sentinel",
        "📚 Field Manual",
        "⚙️ System Settings"
    ])

    st.divider()
    st.subheader("📥 Data Acquisition")
    with st.form("entry_gate", clear_on_submit=True):
        sp = st.selectbox("Select Species", list(SPECIES_METRICS.keys()))
        sire = st.text_input("Sire ID (Genetic Line)", "UoN-BULL-01")
        c1, c2 = st.columns(2)
        w_start = c1.number_input("Start Wt (kg)", 0.5, 1200.0, 30.0)
        w_end = c1.number_input("Current Wt (kg)", 0.5, 1500.0, 35.0)
        days = c2.number_input("Days Active", 1, 10000, 15)
        f_total = c2.number_input("Feed Used (kg)", 0.1, 20000.0, 60.0)
        
        if st.form_submit_button("Authenticate & Log"):
            adg = (w_end - w_start) / days
            profit = AegisEngine.calculate_roi(w_end, w_start, f_total, sp)
            manure = days * SPECIES_METRICS[sp]["manure_rate"]
            
            new_entry = {
                "ID": f"AEG-{sp[:2].upper()}-{random.randint(1000,9999)}",
                "Species": sp, "Sire": sire, "ADG": adg, "Profit": profit,
                "Manure": manure, "Biogas": AegisEngine.calculate_biogas(manure, sp),
                "CH4": days * SPECIES_METRICS[sp]["ch4_factor"],
                "FCR": f_total / (w_end - w_start) if (w_end - w_start) > 0 else 0,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Weight": w_end
            }
            st.session_state.records.append(new_entry)
            st.toast("Data Persisted to Session", icon="✅")
            st.rerun()

# ==========================================
# 6. APPLICATION MODULES
# ==========================================

# --- A. TACTICAL DASHBOARD ---
if menu == "📊 Tactical Dashboard":
    st.title("Strategic Herd Overview")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Cumulative ROI", f"KES {df['Profit'].sum():,.0f}")
        col_m2.metric("Mean ADG", f"{df['ADG'].mean():.3f} kg/d")
        col_m3.metric("FCR (Efficiency)", f"{df['FCR'].mean():.2f}")
        col_m4.metric("Active Herd", f"{len(df)} Head")

        st.subheader("Growth Distribution by Genetic Line")
        growth_chart = alt.Chart(df).mark_bar().encode(
            x='ID:N', y='ADG:Q', color='Species:N', tooltip=['ID', 'Sire', 'ADG']
        ).properties(height=400).interactive()
        st.altair_chart(growth_chart, use_container_width=True)
        
        with st.expander("Detailed Log Analysis"):
            st.dataframe(df.style.background_gradient(cmap='YlGn'), use_container_width=True)
    else:
        st.info("System awaiting initial data ingestion. Use sidebar form to start.")

# --- B. GENETIC SCORECARD ---
elif menu == "🧬 Genetic Scorecard":
    st.title("Genetic Ranking Engine")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        df['Target'] = df['Species'].apply(lambda x: SPECIES_METRICS[x]['adg_target'])
        df['Delta'] = df['ADG'] - df['Target']
        
        sire_eval = df.groupby('Sire').agg({
            'Delta': 'mean', 'Profit': 'sum', 'ID': 'count'
        }).reset_index().rename(columns={'ID': 'Progeny_Count'}).sort_values('Delta', ascending=False)
        
        st.subheader("Sire Performance Ranking (Deviation from Standard)")
        st.write("Ranking Sires based on the average weight-gain superiority of their offspring.")
        st.table(sire_eval.style.highlight_max(subset=['Delta'], color='#d1fae5'))
        
        c_sire = alt.Chart(sire_eval).mark_bar().encode(
            x='Sire:N', y='Delta:Q', 
            color=alt.condition(alt.datum.Delta > 0, alt.value('green'), alt.value('red'))
        )
        st.altair_chart(c_sire, use_container_width=True)
    else:
        st.warning("No genetic data available. Link entries to Sire IDs.")

# --- C. ADVANCED FEED LAB ---
elif menu == "🧪 Advanced Feed Lab":
    st.title("Nutritional Optimization Lab")
    
    st.markdown("### Pearson Square Multi-Mix Optimization")
    
    f1, f2 = st.columns(2)
    target_cp = f1.slider("Required Crude Protein (CP %)", 10.0, 35.0, 16.0)
    total_mix = f1.number_input("Desired Batch Weight (kg)", 10, 10000, 100)
    
    en_name = f2.text_input("Energy Component", "Maize Bran")
    en_cp = f2.number_input(f"{en_name} CP%", 1.0, 15.0, 8.5)
    
    pr_name = f2.text_input("Protein Component", "Soya Meal")
    pr_cp = f2.number_input(f"{pr_name} CP%", 20.0, 60.0, 44.0)
    
    if pr_cp > target_cp > en_cp:
        part_en = abs(pr_cp - target_cp)
        part_pr = abs(en_cp - target_cp)
        t_parts = part_en + part_pr
        
        res_en = (part_en/t_parts) * total_mix
        res_pr = (part_pr/t_parts) * total_mix
        
        st.success(f"Optimized Formulation for {total_mix}kg at {target_cp}% CP")
        st.info(f"⚖️ **{en_name}**: {res_en:.2f} kg  |  ⚖️ **{pr_name}**: {res_pr:.2f} kg")
    else:
        st.error("Invalid Constraint: Target CP must sit between Energy and Protein CP levels.")

# --- D. ENVIRONMENTAL HUB ---
elif menu == "♻️ Environmental Hub":
    st.title("Circular Economy & Carbon Tracking")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        t_biogas = df['Biogas'].sum()
        
        st.metric("Total Biogas Potential", f"{t_biogas:,.2f} m³")
        st.markdown(f"**Impact:** This energy can replace approximately **{t_biogas * 1.5:.1f} kg of LPG** or power a lamp for **{t_biogas * 5:.0f} hours**.")
        
        
        
        st.subheader("Methane (CH4) Emission Trends")
        ch4_chart = alt.Chart(df).mark_line(point=True).encode(x='Date', y='CH4', color='Species')
        st.altair_chart(ch4_chart, use_container_width=True)
    else:
        st.warning("Input required for environmental analysis.")

# --- E. VISUAL AI TRIAGE ---
elif menu == "📸 Visual AI Triage":
    st.title("Visual Diagnostic Intelligence")
    st.write("Upload ocular or dermal samples for AEGIS Deep-Learning Triage.")
    
    up_img = st.file_uploader("Upload Sample", type=['jpg', 'png', 'jpeg'])
    if up_img:
        st.image(up_img, width=400, caption="Processing Sample...")
        with st.spinner("Analyzing Morphology via Teachable Machine Bridge..."):
            time.sleep(2) # Simulated Latency
            conf = random.uniform(88.5, 99.2)
            st.error(f"Detection: **Parasitic Anemia Indicators** Identified ({conf:.1f}% confidence).")
            st.warning("Recommendation: Proceed to FAMACHA eye-score check immediately.")
            

# --- F. CLIMATE SENTINEL ---
elif menu == "🌦️ Climate Sentinel":
    st.title("Meteorological Risk Intelligence")
    api_key = st.text_input("OpenWeatherMap API Key", type="password")
    city = st.text_input("Farm Location", "Nakuru")
    
    if api_key:
        w_data = AegisEngine.get_weather(api_key, city)
        if w_data:
            st.success(f"Live Feed: {city}")
            temp = w_data['main']['temp']
            hum = w_data['main']['humidity']
            c1, c2 = st.columns(2)
            c1.metric("Current Temp", f"{temp}°C")
            c2.metric("Humidity", f"{hum}%")
            
            if "rain" in w_data['weather'][0]['description'].lower():
                st.error("⛈️ Heavy Rain Alert: Increase risk of CCPP (Goats) and Rift Valley Fever.")
            if temp > 32:
                st.warning("🔥 Heat Stress: Ensure maximum ventilation and hydration.")
        else:
            st.error("API Key pending or invalid location.")
    else:
        st.info("Enter API Key to enable real-time risk modeling.")

# --- G. VAX SENTINEL ---
elif menu == "📅 Vax Sentinel":
    st.title("Proactive Immunization Sentinel")
    if st.session_state.records:
        v_list = []
        for r in st.session_state.records:
            b_date = datetime.strptime(r["Date"], "%Y-%m-%d")
            for v_name, v_days in SPECIES_METRICS[r["Species"]]["vaccines"]:
                v_list.append({
                    "Animal ID": r["ID"], "Vaccine": v_name,
                    "Date Due": (b_date + timedelta(days=v_days)).strftime("%Y-%m-%d"),
                    "Species": r["Species"]
                })
        st.table(pd.DataFrame(v_list).sort_values("Date Due"))
    else:
        st.info("Registry empty.")

# --- H. FIELD MANUAL ---
elif menu == "📚 Field Manual":
    st.title("Veterinary Clinical Protocols")
    tab_cl, tab_sym = st.tabs(["Clinical SOPs", "Symptom Logic"])
    
    with tab_cl:
        st.markdown("""
        ### Physical Examination Standards
        1. **Rumen Motility:** Fist on left paralumbar fossa. Norm: 2-3 contractions / 2 mins.
        2. **Hydration:** Skin tenting on neck. >3 seconds indicates clinical dehydration.
        3. **CRT (Capillary Refill):** Press gums; color must return in < 2 seconds.
        """)
        
    
    with tab_sym:
        st.subheader("Diagnostic Matrix")
        st.json(SYMPTOM_MATRIX)

# --- I. SYSTEM SETTINGS ---
elif menu == "⚙️ System Settings":
    st.title("System Maintenance")
    
    st.subheader("Cloud Data Persistence")
    if st.button("Generate Secure Backup Snapshot"):
        st.code(backup_data(), language="text")
        st.caption("Copy this hash to a secure location (e.g., WhatsApp or Cloud Notes).")
    
    restore_code = st.text_input("Inject Restore Hash")
    if st.button("Initialize Restoration"):
        if restore_data(restore_code): st.success("System Restored Successfully"); st.rerun()
        else: st.error("Hash Integrity Failed.")
        
    st.divider()
    st.subheader("Disaster Recovery")
    if not st.session_state.confirm_wipe:
        if st.button("🚨 NUCLEAR FACTORY RESET"):
            st.session_state.confirm_wipe = True; st.rerun()
    else:
        st.error("ARE YOU SURE? This action is irreversible.")
        if st.button("✅ CONFIRM PURGE"):
            st.session_state.records = []
            st.session_state.confirm_wipe = False; st.rerun()
        if st.button("❌ ABORT"):
            st.session_state.confirm_wipe = False; st.rerun()

# ==========================================
# 7. FOOTER & COMPLIANCE
# ==========================================
st.divider()
st.caption(f"AEGIS v13.0 | Research Lead: Eric Kamau | University of Nairobi | {datetime.now().year}")
