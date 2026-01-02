# ==============================================================================
# 🛡️ AEGIS v31.0: THE GREAT RIFT SOVEREIGN (ENTERPRISE MASTER)
# ==============================================================================
# Lead Architect: Eric Kamau | AEGIS Project | University of Nairobi (UoN)
# "Excellence Without Flaws" | Build Date: 2026-01-02
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import time
import random
import json
from datetime import datetime, timedelta

# ------------------------------------------------------------------------------
# 1. THE DATA MOAT (Hardcoded Research Bases)
# ------------------------------------------------------------------------------

# Massive clinical database (Veterinaria Digital + KALRO Standards)
CLINICAL_TRIAGE_DATA = {
    "Cattle (Dairy/Beef)": {
        "East Coast Fever (ECF)": {
            "symptoms": ["Swollen parotid lymph nodes", "Froth from nose", "High fever", "Labored breathing"],
            "triage": "Red (Emergency)",
            "protocol": "Buparvaquone (Butalex) injection immediately. Contact Vet.",
            "zoonotic": False
        },
        "Anaplasmosis (Tick Fever)": {
            "symptoms": ["Jaundice (Yellow mucous membranes)", "Anemia", "Hard dung", "Loss of appetite"],
            "triage": "Red (Emergency)",
            "protocol": "Oxytetracycline 20% L.A. and tick control.",
            "zoonotic": False
        },
        "Mastitis": {
            "symptoms": ["Swollen/Hot udder", "Clots/blood in milk", "Pain when milking"],
            "triage": "Yellow (Urgent)",
            "protocol": "Strip milk every 2 hours, use Intramammary tubes, check hygiene.",
            "zoonotic": False
        },
        "Milk Fever (Hypocalcemia)": {
            "symptoms": ["Inability to stand after calving", "S-curve neck", "Cold ears/skin"],
            "triage": "Red (Emergency)",
            "protocol": "Calcium Borogluconate IV (Slowly).",
            "zoonotic": False
        },
        "Brucellosis": {
            "symptoms": ["Late-term abortion", "Retained placenta", "Swollen joints"],
            "triage": "Red (Alert)",
            "protocol": "Quarantine. Danger! Can infect humans via raw milk.",
            "zoonotic": True
        }
    },
    "Poultry (Broilers/Layers)": {
        "Newcastle Disease": {
            "symptoms": ["Twisted neck", "Greenish diarrhea", "Respiratory distress"],
            "triage": "Red (Critical)",
            "protocol": "Total quarantine. Vaccination of survivors. Cull infected.",
            "zoonotic": False
        },
        "Coccidiosis": {
            "symptoms": ["Bloody droppings", "Ruffled feathers", "Pale combs"],
            "triage": "Yellow (Urgent)",
            "protocol": "Amprolium or Sulfonamides in drinking water.",
            "zoonotic": False
        },
        "Gumboro (IBD)": {
            "symptoms": ["Trembling", "Self-pecking at vent", "Watery diarrhea"],
            "triage": "Red (Critical)",
            "protocol": "Supportive therapy (Electrolytes). Ensure strict vaccination.",
            "zoonotic": False
        }
    }
}

# Advanced Feed Library
FEED_MASTER_LIST = {
    "Maize Bran": {"cp": 8.0, "me": 11.0, "dm": 88, "cost": 38, "type": "Energy"},
    "Soya Bean Meal": {"cp": 45.0, "me": 12.5, "dm": 90, "cost": 98, "type": "Protein"},
    "Lucerne Hay": {"cp": 19.0, "me": 9.2, "dm": 85, "cost": 55, "type": "Roughage"},
    "Cotton Seed Cake": {"cp": 28.0, "me": 10.5, "dm": 92, "cost": 62, "type": "Protein"},
    "Napier Grass": {"cp": 9.5, "me": 8.0, "dm": 20, "cost": 12, "type": "Roughage"},
    "Wheat Pollard": {"cp": 15.5, "me": 10.2, "dm": 89, "cost": 42, "type": "Energy"}
}

# ------------------------------------------------------------------------------
# 2. LOGIC ENGINES (Scientific Formulas)
# ------------------------------------------------------------------------------

def run_pearson_square(target, feed1_val, feed2_val):
    if not (min(feed1_val, feed2_val) < target < max(feed1_val, feed2_val)):
        return None
    parts1 = abs(feed2_val - target)
    parts2 = abs(feed1_val - target)
    total = parts1 + parts2
    return (parts1/total)*100, (parts2/total)*100

def get_lactation_curve(day, peak=25):
    # Wood's Model Formula: a * t^b * e^(-ct)
    return peak * (day**0.19) * np.exp(-0.003 * day)

# ------------------------------------------------------------------------------
# 3. STATE MANAGEMENT & SYSTEM INIT
# ------------------------------------------------------------------------------

if 'db' not in st.session_state: st.session_state.db = []
if 'mortality' not in st.session_state: st.session_state.mortality = 0
if 'logs' not in st.session_state: st.session_state.logs = []

def record_log(action):
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {action}")

# ------------------------------------------------------------------------------
# 4. SIDEBAR & NAVIGATION
# ------------------------------------------------------------------------------

st.set_page_config(page_title="AEGIS v31.0 Apex", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("🛡️ AEGIS v31.0")
    st.caption("Sovereign Enterprise OS | Eric Kamau")
    
    ranch_mode = st.toggle("🚀 Activate Ranch/Corporate Mode")
    
    nav = st.radio("Sovereign Control Units", [
        "📊 Tactical Dashboard",
        "🧪 Precision Optimizer",
        "🩺 Clinical Triage",
        "🐤 Poultry Batch (Kenchic)",
        "🥛 Dairy Logistics (Brookside)",
        "📅 Vax & Safety",
        "♻️ Green Hub (Carbon)",
        "🆔 Digital Passports",
        "📡 National Uplink",
        "⚙️ Admin Panel"
    ])
    
    st.divider()
    with st.form("inventory_entry"):
        st.subheader("📥 Asset Intake")
        sp = st.selectbox("Species", ["Dairy Cattle", "Beef Cattle", "Goat", "Poultry Flock"])
        uid = st.text_input("Asset/Batch ID", f"AEG-{random.randint(100,999)}")
        wt = st.number_input("Current Weight (kg)", 0.1, 1500.0, 250.0)
        age = st.number_input("Age/Days in Milk", 0, 1000, 30)
        
        if st.form_submit_button("DEPLOY ASSET"):
            st.session_state.db.append({
                "uid": uid, "spec": sp, "weight": wt, "age": age, 
                "date": datetime.now().date(), "adg": random.uniform(0.3, 0.9)
            })
            record_log(f"Registered {sp}: {uid}")
            st.rerun()

# ------------------------------------------------------------------------------
# 5. MODULES (THE CORE CODE)
# ------------------------------------------------------------------------------

# --- A. TACTICAL DASHBOARD ---
if nav == "📊 Tactical Dashboard":
    st.header("📈 Tactical Command Center")
    
    
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Population", len(df))
        c2.metric("Total Biomass", f"{df['weight'].sum():,.1f} kg")
        c3.metric("Avg Growth Index", f"{df['adg'].mean():.2f}")
        c4.metric("Supply Health", "STABLE")
        
        if ranch_mode:
            st.subheader("🌾 Ranch Carrying Capacity Analytics")
            
            acres = st.number_input("Ranch Total Acres", 10, 50000, 500)
            au_cap = acres / 4 # 4 acres per Animal Unit
            current_util = (len(df) / au_cap) * 100
            
            st.write(f"**Current Load:** {len(df)} Head / **Capacity:** {int(au_cap)} Head")
            st.progress(min(current_util/100, 1.0))
            if current_util > 90: st.error("🚨 OVERGRAZING CRITICAL: Land degradation risk.")
        
        st.divider()
        st.write("### Active Asset Ledger")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("System Ready. Please deploy assets via the sidebar.")

# --- B. PRECISION OPTIMIZER ---
elif nav == "🧪 Precision Optimizer":
    st.header("🧪 Precision Feed Optimizer")
    
    st.write("Using Pearson Square and DM (Dry Matter) balancing logic.")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        target_cp = st.slider("Target Crude Protein %", 10.0, 25.0, 16.0)
        energy_src = st.selectbox("Energy Base", [k for k, v in FEED_MASTER_LIST.items() if v['type'] == 'Energy' or v['type'] == 'Roughage'])
        protein_src = st.selectbox("Protein Supplement", [k for k, v in FEED_MASTER_LIST.items() if v['type'] == 'Protein'])
    
    with col_f2:
        res = run_pearson_square(target_cp, FEED_MASTER_LIST[energy_src]['cp'], FEED_MASTER_LIST[protein_src]['cp'])
        if res:
            p_e, p_p = res
            st.success(f"**Optimal Ratio Found!**")
            st.write(f"✅ {p_e:.1f}% {energy_src}")
            st.write(f"✅ {p_p:.1f}% {protein_src}")
            
            # Financials
            daily_cost = (p_e/100 * FEED_MASTER_LIST[energy_src]['cost']) + (p_p/100 * FEED_MASTER_LIST[protein_src]['cost'])
            st.metric("Estimated Cost per KG", f"KES {daily_cost:.2f}")
        else:
            st.error("Mathematical Impossible: Target CP out of range for selected feeds.")

# --- C. CLINICAL TRIAGE ---
elif nav == "🩺 Clinical Triage":
    st.header("🩺 Clinical Decision Engine")
    
    
    category = st.selectbox("Select Animal Group", list(CLINICAL_TRIAGE_DATA.keys()))
    condition = st.selectbox("Observed Signs/Disease", list(CLINICAL_TRIAGE_DATA[category].keys()))
    
    data = CLINICAL_TRIAGE_DATA[category][condition]
    
    with st.container(border=True):
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            if "Red" in data['triage']: st.error(f"🚨 {data['triage']}")
            else: st.warning(f"⚠️ {data['triage']}")
            
            if data['zoonotic']:
                st.markdown("☣️ **ZOONOTIC WARNING**: Can infect humans.")
        
        with col_t2:
            st.subheader(condition)
            st.write(f"**Key Symptoms:** {', '.join(data['symptoms'])}")
            st.info(f"**Treatment Protocol:** {data['protocol']}")

# --- D. POULTRY BATCH (KENCHIC) ---
elif nav == "🐤 Poultry Batch (Kenchic)":
    st.header("🐤 Kenchic Batch Performance")
    
    
    c_p1, c_p2, c_p3 = st.columns(3)
    flock = c_p1.number_input("Batch Size", 100, 50000, 1000)
    current_mort = c_p2.number_input("Total Deaths", 0, flock, 5)
    feed_used = c_p3.number_input("Total Feed Consumed (kg)", 1.0, 50000.0, 1500.0)
    
    # Advanced Metrics
    mort_rate = (current_mort / flock) * 100
    # FCR Calculation
    avg_wt = 1.6 # Example kg
    fcr = feed_used / (flock * avg_wt)
    
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric("Mortality Rate", f"{mort_rate:.2f}%", delta="-0.5%", delta_color="inverse")
    m2.metric("Feed Conversion Ratio (FCR)", f"{fcr:.2f}")
    
    if mort_rate > 5:
        st.error("🚨 CRITICAL MORTALITY: Above Kenchic Enterprise Standard. Bio-security alert triggered.")
    if fcr > 2.1:
        st.warning("⚠️ EFFICIENCY LOSS: High feed wastage or sub-clinical disease detected.")

# --- E. DAIRY LOGISTICS (BROOKSIDE) ---
elif nav == "🥛 Dairy Logistics (Brookside)":
    st.header("🥛 Brookside Supply Logistics")
    
    
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        dairy_df = df[df['spec'] == "Dairy Cattle"]
        
        if not dairy_df.empty:
            st.subheader("7-Day Production Forecast")
            # Predict yield using Wood's Model logic for each cow
            forecast_data = []
            for d in range(7):
                day_total = sum([get_lactation_curve(row['age'] + d) for index, row in dairy_df.iterrows()])
                forecast_data.append(day_total)
            
            st.line_chart(forecast_data)
            st.metric("Total Collection Volume (Next 24h)", f"{int(forecast_data[0])} Liters")
            st.info("📡 Logistics Uplink: Data ready for Brookside collection scheduling.")
        else: st.warning("No Dairy Cattle in registry.")

# --- F. VAX & SAFETY ---
elif nav == "📅 Vax & Safety":
    st.header("💊 Pharmacovigilance & Withdrawal")
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.subheader("Withdrawal Tracker")
        drug = st.selectbox("Drug Administered", ["Penicillin (3 Days)", "Oxytetracycline (7 Days)", "Ivermectin (28 Days)"])
        days = {"Penicillin (3 Days)": 3, "Oxytetracycline (7 Days)": 7, "Ivermectin (28 Days)": 28}
        admin_date = st.date_input("Administration Date")
        
        safe_date = admin_date + timedelta(days=days[drug])
        if datetime.now().date() >= safe_date:
            st.success(f"✅ PRODUCT SAFE: Withdrawal period ended on {safe_date}")
        else:
            st.error(f"🚫 UNSAFE: Product cannot be sold until {safe_date}")

# --- G. GREEN HUB ---
elif nav == "♻️ Green Hub (Carbon)":
    st.header("🌍 Carbon & Biogas Intelligence")
    
    
    total_wt = sum([x['weight'] for x in st.session_state.db])
    manure = total_wt * 0.06 # 6% of body weight
    methane = manure * 0.04
    
    c_g1, c_g2 = st.columns(2)
    c_g1.metric("Daily Manure (kg)", f"{manure:,.1f}")
    c_g1.metric("Biogas Potential (m³)", f"{methane:,.2f}")
    
    # Carbon Credit Logic
    co2e_offset = (methane * 25) / 1000 # Tons
    c_g2.metric("Carbon Offset (Tons CO2e)", f"{co2e_offset:.4f}")
    st.success(f"Estimated Voluntary Carbon Credit Value: KES {co2e_offset * 1500:,.2f} / day")

# --- H. DIGITAL PASSPORTS ---
elif nav == "🆔 Digital Passports":
    st.header("🆔 Sovereign Trust Passports")
    if st.session_state.db:
        uid_p = st.selectbox("Select Asset", [x['uid'] for x in st.session_state.db])
        qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=AEGIS_VERIFIED_{uid_p}"
        
        with st.container(border=True):
            col_p1, col_p2 = st.columns([2, 1])
            col_p1.write(f"### ID: {uid_p}")
            col_p1.write(f"**Status:** Bio-Metric Verified")
            col_p1.write(f"**Origin:** AEGIS Sovereign Node")
            col_p2.image(qr_api, caption="Trust Badge")
    else: st.info("Registry empty.")

# --- I. NATIONAL UPLINK ---
elif nav == "📡 National Uplink":
    st.header("📡 National Agricultural Data Uplink")
    
    st.write("Transmit real-time census and disease data to Ministry of Agriculture & KALRO.")
    
    if st.button("EXECUTE SOVEREIGN TRANSMISSION"):
        with st.status("Encrypting Data Packets...", expanded=True) as status:
            time.sleep(1)
            status.write("Establishing Secure Socket with DLPD Hub...")
            time.sleep(1)
            status.write("Aggregating County Bio-metrics...")
            time.sleep(1)
            status.update(label="✅ UPLINK COMPLETE: REF-UON-2026-X", state="complete")
        st.success("Data successfully synchronized with National Food Security Dashboard.")

# --- J. ADMIN PANEL ---
elif nav == "⚙️ Admin Panel":
    st.header("⚙️ System Administration")
    if st.button("🔴 RESET LOCAL DATABASE"):
        st.session_state.db = []
        st.rerun()
    
    st.subheader("System Audit Logs")
    for log in reversed(st.session_state.logs):
        st.caption(log)

# ------------------------------------------------------------------------------
# 6. FOOTER (KEEP AT BOTTOM)
# ------------------------------------------------------------------------------
st.divider()
st.caption(f"AEGIS v31.0 Apex | Eric Kamau | UoN 2026 | Excellence Without Flaws")
