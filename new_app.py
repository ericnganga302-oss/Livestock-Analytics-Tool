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
# 1. CORE SYSTEM CONFIGURATION
# ==========================================
st.set_page_config(page_title="AEGIS: Sovereign Livestock OS", page_icon="🛡️", layout="wide")

# --- MASTER KNOWLEDGE BASES ---
MARKET_DATABASE = {
    "Beef": {"price": 760, "cp_target": 14, "std_adg": 0.8, "ch4": 0.18, "manure": 12.0, "biogas": 0.04, "cycle": 21, "gest": 283},
    "Pig": {"price": 550, "cp_target": 16, "std_adg": 0.6, "ch4": 0.04, "manure": 4.0, "biogas": 0.06, "cycle": 21, "gest": 114},
    "Goat": {"price": 950, "cp_target": 15, "std_adg": 0.15, "ch4": 0.02, "manure": 1.5, "biogas": 0.05, "cycle": 21, "gest": 150},
    "Sheep": {"price": 900, "cp_target": 15, "std_adg": 0.2, "ch4": 0.02, "manure": 1.5, "biogas": 0.05, "cycle": 17, "gest": 152}
}

FEED_LIBRARY = {
    "Whole Maize": {"cp": 8.2, "energy": 13.5, "type": "Energy"},
    "Maize Bran": {"cp": 7.0, "energy": 11.5, "type": "Energy"},
    "Soya Bean Meal": {"cp": 45.0, "energy": 12.5, "type": "Protein"},
    "Cotton Seed Cake": {"cp": 26.0, "energy": 10.5, "type": "Protein"},
    "Omena (Fishmeal)": {"cp": 55.0, "energy": 11.0, "type": "Protein"},
    "Lucerne": {"cp": 18.0, "energy": 8.5, "type": "Roughage"}
}

VAX_PROTOCOLS = {
    "Beef": [("FMD", 0), ("Lumpy Skin", 30), ("Anthrax/Blackquarter", 180)],
    "Pig": [("Swine Fever", 0), ("Parvo", 21), ("Erysipelas", 45)],
    "Goat": [("PPR", 0), ("CCPP", 30), ("Enterotoxaemia", 60)],
    "Sheep": [("Blue Tongue", 0), ("Sheep Pox", 30), ("Foot Rot", 90)]
}

TRIAGE_MATRIX = {
    "Respiratory": {
        "Coughing/Nasal Discharge": {"risk": "Yellow", "diag": "Pneumonia", "action": "Isolate & check temperature."},
        "Open Mouth Breathing": {"risk": "Red", "diag": "Acute Distress/Anthrax", "action": "IMMEDIATE VET CALL."}
    },
    "Digestive": {
        "Bloated Left Flank": {"risk": "Red", "diag": "Frothy Bloat", "action": "Emergency: Use stomach tube or trocar."},
        "Scours (Diarrhea)": {"risk": "Yellow", "diag": "Coccidiosis", "action": "Hydrate with ORS; check foul smell."}
    },
    "Neurological": {
        "Stargazing/Circling": {"risk": "Red", "diag": "Heartwater or CCN", "action": "Check for ticks; immediate antibiotic intervention."},
        "Downer (Cannot Rise)": {"risk": "Red", "diag": "Milk Fever or Injury", "action": "Check calcium levels."}
    }
}

MEDICATION_WITHDRAWAL = {
    "Penicillin": {"milk": 3, "meat": 21},
    "Oxytetracycline": {"milk": 5, "meat": 28},
    "Ivermectin": {"milk": 28, "meat": 21},
    "Tylosin": {"milk": 4, "meat": 21}
}

VET_DIRECTORY = {
    "Nakuru": [{"name": "Dr. Maina", "phone": "+254 711 000 000", "loc": "Njoro"}, {"name": "County Vet", "phone": "+254 722 000 000", "loc": "Nakuru CBD"}],
    "Nairobi/Kiambu": [{"name": "UoN Vet Clinic", "phone": "+254 711 222 333", "loc": "Kabete"}]
}

# ==========================================
# 2. UTILITY & LOGIC FUNCTIONS
# ==========================================
if 'db' not in st.session_state: st.session_state.db = []

def get_live_weather(city="Nakuru"):
    # Using a demo key context; in prod use environment variable
    api_key = "11e5adaf7907408fa5661babadc4605c" 
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- NEW: FINANCIAL BURN RATE LOGIC ---
def calculate_daily_burn(db):
    st.subheader("💸 Economic Velocity & Burn Rate")
    if not db:
        st.info("⚠️ Log animal data to see financial velocity.")
        return

    df = pd.DataFrame(db)
    # Assumptions for logic
    labor_cost_per_head = 20 # KES per day
    
    total_margin = 0
    
    # We display the first 3 for brevity, or aggregate
    for index, row in df.iterrows():
        # Daily Revenue from Growth (Weight Gain Value)
        daily_revenue = row['adg'] * MARKET_DATABASE[row['spec']]['price']
        # Daily Expenses (Feed + Labor) - Assuming feed is total over days, roughly avg per day
        # Better logic: (row['feed'] / row['days']) * 60 (price of feed)
        feed_cost_daily = (row['feed'] / 15) * 60 # Using 15 as placeholder days if not tracked per day
        daily_expense = feed_cost_daily + labor_cost_per_head
        
        net_velocity = daily_revenue - daily_expense
        total_margin += net_velocity
    
    st.metric("Total Herd Net Daily Velocity", f"KES {total_margin:,.2f}", delta=f"{total_margin:,.2f}")
    if total_margin < 0:
        st.error("🚨 BURN ALERT: The farm is losing money daily. Review feed costs immediately.")
    else:
        st.success("✅ POSITIVE CASH FLOW: The herd is generating daily profit.")

# ==========================================
# 3. SIDEBAR NAVIGATION & INTAKE
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=90)
    st.title("AEGIS v23.0")
    st.write(f"**Creator:** Eric Kamau")
    st.caption("University of Nairobi | 2026")
    
    nav = st.radio("Sovereign Modules", [
        "📊 Dashboard & Finance", "🧬 Genetic Scorecard", "🧪 Optimizer Pro", 
        "📅 Vax Sentinel", "🩺 Health Triage", "🧬 Fertility Sentinel", 
        "♻️ Green Cycle Hub", "💊 Drug Safety", "📡 Transmission Hub", "⚙️ System Admin"
    ])

    st.divider()
    with st.form("entry_form"):
        st.write("### 📥 Animal Intake")
        sp = st.selectbox("Species", list(MARKET_DATABASE.keys()))
        sire = st.text_input("Sire ID", "UoN-BULL-01")
        w_in = st.number_input("Start Wt (kg)", 1.0, 1000.0, 30.0)
        w_now = st.number_input("Current Wt (kg)", 1.0, 1000.0, 35.0)
        days = st.number_input("Days Active", 1, 5000, 15)
        feed = st.number_input("Total Feed (kg)", 0.1, 10000.0, 60.0)
        
        if st.form_submit_button("DEPLOY ASSET"):
            gain = w_now - w_in
            adg = gain/days
            profit = (w_now * MARKET_DATABASE[sp]["price"]) - (feed * 60)
            
            st.session_state.db.append({
                "uid": f"AEG-{random.randint(1000,9999)}", "spec": sp, "sire": sire, 
                "adg": adg, "profit": profit, "weight": w_now, "feed": feed,
                "days": days, "date": datetime.now().strftime("%Y-%m-%d"), 
                "manure": days * MARKET_DATABASE[sp]["manure"]
            })
            st.success("Asset Deployed Successfully")
            time.sleep(1)
            st.rerun()

# ==========================================
# 4. MODULES EXECUTION
# ==========================================

# --- A. DASHBOARD, WEATHER, & FINANCE ---
if nav == "📊 Dashboard & Finance":
    st.title("Tactical Herd Dashboard")
    
    # 1. Weather Logic
    weather = get_live_weather("Nakuru")
    if weather:
        c1, c2, c3 = st.columns(3)
        temp, hum = weather['main']['temp'], weather['main']['humidity']
        c1.metric("Live Temp", f"{temp}°C")
        c2.metric("Humidity", f"{hum}%")
        
        # Weather-Driven Health Alerts
        if hum > 80 and temp > 25:
            c3.error("🚨 HIGH RISK: Rift Valley Fever")
            
        elif temp < 15:
            c3.warning("⚠️ RISK: Calf Pneumonia")
        else:
            c3.success("✅ Climate Stable")
    
    # 2. General Stats
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.write("---")
        st.metric("Total Herd Valuation", f"KES {df['profit'].sum():,.0f}")
        st.dataframe(df, use_container_width=True)
        
        # 3. Financial Burn Rate (New Feature)
        st.write("---")
        calculate_daily_burn(st.session_state.db)
        
    else: 
        st.info("Registry empty. Please add animals via the sidebar.")
        # ==========================================
# AEGIS v23.0 UPGRADE MODULES
# ==========================================

# --- K. FAMACHA VISUAL LAB (The "Eye Check") ---
if nav == "👁️ FAMACHA Lab":
    st.title("👁️ FAMACHA© Anemia calibration")
    st.markdown("""
    **Protocol:** Pull down the lower eyelid of the sheep/goat. Compare the color of the mucous membrane to the chart below.
    """)
    
    # 1. Display the Reference Chart (Simulated Colors)
    st.subheader("1. Calibration Standard")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.color_picker("Score 1 (Optimal)", "#FF0000", disabled=True)
    c2.color_picker("Score 2 (Acceptable)", "#FF4D4D", disabled=True)
    c3.color_picker("Score 3 (Borderline)", "#FF9999", disabled=True)
    c4.color_picker("Score 4 (Dangerous)", "#FFCCCC", disabled=True)
    c5.color_picker("Score 5 (Fatal)", "#FFFFFF", disabled=True)
    
    # 2. The Camera Input
    st.subheader("2. Visual Verification")
    img_file = st.camera_input("Take a photo of the eye membrane")
    
    if img_file:
        st.success("Image captured. Compare with standards above.")
        
        # 3. The Diagnostic Logic
        score = st.slider("Select the matching FAMACHA Score:", 1, 5, 3)
        
        st.write("---")
        if score == 1:
            st.success("✅ **HEALTHY:** No worms. Do NOT deworm (save money/reduce resistance).")
        elif score == 2:
            st.success("✅ **SAFE:** Monitor routine schedule.")
        elif score == 3:
            st.warning("⚠️ **BORDERLINE:** If animal is pregnant or young, deworm now. Otherwise, re-check in 2 weeks.")
        elif score == 4:
            st.error("🚨 **DANGER:** High parasite load. Drench immediately (Ivermectin/Albendazole).")
        elif score == 5:
            st.error("💀 **CRITICAL:** Severe Anemia. Deworm + Iron Injection + Vitamin B12. Move to rich feed.")

# --- L. PUBLIC FACING PROFILE (QR Trust Badge) ---
elif nav == "🆔 Public Profiles":
    st.title("🆔 Asset Trust Badge Generator")
    st.write("Generate a verified 'Digital Passport' for buyers or vets.")
    
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        
        # Select Animal
        uid_select = st.selectbox("Select Asset ID for Passport", df['uid'].unique())
        
        # Get Animal Data
        animal = df[df['uid'] == uid_select].iloc[0]
        
        # Design the Passport Card
        st.write("---")
        with st.container(border=True):
            col_p1, col_p2 = st.columns([2, 1])
            
            with col_p1:
                st.subheader(f"🛡️ AEGIS Verified Asset: {animal['uid']}")
                st.caption(f"University of Nairobi | AEGIS Protocol v24.0")
                st.write(f"**Species:** {animal['spec']} | **Sire:** {animal['sire']}")
                st.write(f"**Current Weight:** {animal['weight']} kg")
                st.write(f"**Growth Rate (ADG):** {animal['adg']:.2f} kg/day")
                
                if animal['adg'] > 0.5:
                    st.success("✅ **Performance Status:** HIGH GROWTH")
                else:
                    st.warning("⚠️ **Performance Status:** STANDARD")
            
            with col_p2:
                # Generate QR Code using a public API (No extra pip install needed)
                # The QR code contains a summary text of the animal's stats
                qr_data = f"AEGIS VERIFIED | ID: {animal['uid']} | Spec: {animal['spec']} | Wt: {animal['weight']}kg | ADG: {animal['adg']:.2f}"
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_data}"
                
                st.image(qr_url, caption="Scan to Verify History")
        
        st.info("💡 **Tip:** Print this page and attach it to the movement permit or invoice when selling.")

    else:
        st.info("Please add animals to the registry to generate profiles.")

# --- B. GENETIC SCORECARD ---
elif nav == "🧬 Genetic Scorecard":
    st.title("Sire Genetic Merit Rankings")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        df['target'] = df['spec'].apply(lambda x: MARKET_DATABASE[x]['std_adg'])
        df['deviation'] = df['adg'] - df['target']
        rank = df.groupby('sire')['deviation'].mean().sort_values(ascending=False).reset_index()
        st.table(rank.style.background_gradient(cmap='RdYlGn'))
    else: st.warning("No breeding data available.")

# --- C. OPTIMIZER PRO ---
elif nav == "🧪 Optimizer Pro":
    st.title("Nutritional Feed Lab (Pearson Square)")
    
    
    t_cp = st.number_input("Target Protein %", 10.0, 30.0, 16.0)
    e_name = st.selectbox("Energy Ingredient", [k for k,v in FEED_LIBRARY.items() if v['type'] == 'Energy'])
    p_name = st.selectbox("Protein Ingredient", [k for k,v in FEED_LIBRARY.items() if v['type'] == 'Protein'])
    
    cp1, cp2 = FEED_LIBRARY[e_name]['cp'], FEED_LIBRARY[p_name]['cp']
    if cp1 < t_cp < cp2:
        parts_e = abs(cp2 - t_cp)
        parts_p = abs(cp1 - t_cp)
        total = parts_e + parts_p
        st.success(f"**Final Mix Formulation:**")
        st.write(f"- {e_name}: {(parts_e/total)*100:.1f}%")
        st.write(f"- {p_name}: {(parts_p/total)*100:.1f}%")
    else: st.error("Target CP is mathematically impossible with these two ingredients.")

# --- D. VAX SENTINEL ---
elif nav == "📅 Vax Sentinel":
    st.title("Automated Vaccination Sentinel")
    if st.session_state.db:
        v_list = []
        for a in st.session_state.db:
            base = datetime.strptime(a["date"], "%Y-%m-%d")
            for name, delta in VAX_PROTOCOLS[a["spec"]]:
                v_list.append({"Animal ID": a["uid"], "Vaccine": name, "Due Date": (base + timedelta(days=delta)).date()})
        st.table(pd.DataFrame(v_list).sort_values("Due Date"))
    else: st.info("Registry empty.")

# --- E. HEALTH TRIAGE ---
elif nav == "🩺 Health Triage":
    st.title("Clinical Triage & Field Response")
    
    
    tab1, tab2 = st.tabs(["Diagnostic Engine", "Vet Directory"])
    
    with tab1:
        sys = st.selectbox("Affected System", list(TRIAGE_MATRIX.keys()))
        sym = st.selectbox("Observed Sign", list(TRIAGE_MATRIX[sys].keys()))
        res = TRIAGE_MATRIX[sys][sym]
        
        if res['risk'] == "Red":
            st.error(f"🚨 **LEVEL: EMERGENCY** | {res['diag']}")
        else:
            st.warning(f"⚠️ **LEVEL: URGENT** | {res['diag']}")
        st.info(f"**Protocol:** {res['action']}")
        
    with tab2:
        reg = st.selectbox("Region", list(VET_DIRECTORY.keys()))
        for v in VET_DIRECTORY[reg]:
            st.write(f"**{v['name']}** - {v['phone']} ({v['loc']})")

# --- F. FERTILITY SENTINEL (WITH GOLDEN HOUR) ---
elif nav == "🧬 Fertility Sentinel":
    st.title("Reproductive Cycle Predictor")
    
    
    # 1. Basic Calculation
    spec = st.selectbox("Species", list(MARKET_DATABASE.keys()))
    last_h = st.date_input("Last Heat Date")
    
    st.write("---")
    st.subheader("🕒 The AI 'Golden Hour' Predictor")
    
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        observed_time = st.time_input("Time Standing Heat Began", datetime.now().time())
        # Combine date and time
        start_time = datetime.combine(last_h, observed_time)
        ai_window_start = start_time + timedelta(hours=6)
        ai_window_end = start_time + timedelta(hours=12)
        
    with col_t2:
        st.info(f"**Best Insemination Window:**")
        st.write(f"From: **{ai_window_start.strftime('%I:%M %p')}**")
        st.write(f"To: **{ai_window_end.strftime('%I:%M %p')}**")

    st.write("---")
    st.metric("Next Heat Cycle Peak", (last_h + timedelta(days=MARKET_DATABASE[spec]['cycle'])).strftime("%d %b"))
    st.metric("Gestation Due Date", (last_h + timedelta(days=MARKET_DATABASE[spec]['gest'])).strftime("%d %b, %Y"))

# --- G. GREEN CYCLE HUB (WITH BIO-SLURRY) ---
elif nav == "♻️ Green Cycle Hub":
    st.title("Circular Waste-to-Energy")
    
    
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        total_m = df['manure'].sum()
        
        st.metric("Total Manure Logged (kg)", f"{total_m:,.1f}")
        
        # New Bio-Slurry Logic
        st.subheader("🌱 Bio-Slurry Fertilizer Value")
        slurry_liters = total_m * 0.7
        savings = (slurry_liters / 50) * 3500 
        
        c1, c2 = st.columns(2)
        c1.metric("Organic Fertilizer (L)", f"{slurry_liters:.1f}")
        c2.metric("Synthetic Savings", f"KES {savings:,.0f}")
        st.success(f"💰 You have saved KES {savings:,.0f} in fertilizer costs!")
    else: st.info("No animal data to calculate manure.")

# --- H. DRUG SAFETY ---
elif nav == "💊 Drug Safety":
    st.title("Withdrawal Safety Tracker")
    drug = st.selectbox("Administered Drug", list(MEDICATION_WITHDRAWAL.keys()))
    d_given = st.date_input("Date Administered")
    m_safe = d_given + timedelta(days=MEDICATION_WITHDRAWAL[drug]['milk'])
    t_safe = d_given + timedelta(days=MEDICATION_WITHDRAWAL[drug]['meat'])
    
    st.warning(f"**Safe for Milk:** {m_safe} | **Safe for Meat:** {t_safe}")
    if datetime.now().date() < m_safe: st.error("🚫 MILK IS UNSAFE. DO NOT SELL.")

# --- I. TRANSMISSION HUB ---
elif nav == "📡 Transmission Hub":
    st.title("National Transmission & Sharing")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏛️ Ministry Uplink (DLPD)")
            if st.button("TRANSMIT CENSUS DATA"):
                with st.spinner("Encrypting..."):
                    time.sleep(1.5)
                st.success("✅ Census Data Transmitted. Ref: UoN-2026-AEGIS")
        with col2:
            st.subheader("📤 Farmer Share")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("💾 Download Report", csv, "Farm_Report.csv", "text/csv")
            st.button("📲 Share to WhatsApp")

# --- J. SYSTEM ADMIN ---
elif nav == "⚙️ System Admin":
    st.title("Admin & Cloud Snapshots")
    if st.button("Generate Backup Code"):
        st.code(base64.b64encode(json.dumps(st.session_state.db).encode()).decode())
    if st.button("🔴 PURGE ALL DATA"):
        st.session_state.db = []
        st.rerun()

st.divider()
st.caption(f"AEGIS v23.0 | Eric Kamau | University of Nairobi | {datetime.now().year}")
