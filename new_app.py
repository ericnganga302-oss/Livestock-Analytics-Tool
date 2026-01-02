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
# 1. CORE SYSTEM ARCHITECTURE & DATABASE
# ==========================================
st.set_page_config(page_title="AEGIS: Sovereign Livestock OS", page_icon="🛡️", layout="wide")

# Master Knowledge Databases
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
    }
}

MEDICATION_WITHDRAWAL = {
    "Penicillin": {"milk": 3, "meat": 21},
    "Oxytetracycline": {"milk": 5, "meat": 28},
    "Ivermectin": {"milk": 28, "meat": 21}
}

VET_DIRECTORY = {
    "Nakuru": [{"name": "Dr. Maina", "phone": "+254 711 000 000", "loc": "Njoro"}, {"name": "County Vet", "phone": "+254 722 000 000", "loc": "Nakuru CBD"}],
    "Nairobi/Kiambu": [{"name": "UoN Vet Clinic", "phone": "+254 711 222 333", "loc": "Kabete"}]
}

# ==========================================
# 2. SESSION STATE & UTILITIES
# ==========================================
if 'db' not in st.session_state: st.session_state.db = []

def get_live_weather(city="Nakuru"):
    api_key = "11e5adaf7907408fa5661babadc4605c" 
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=90)
    st.title("AEGIS v21.0")
    st.write(f"**Creator:** Eric Kamau")
    
    nav = st.radio("Sovereign Modules", [
        "📊 Tactical Dashboard", "🧬 Genetic Scorecard", "🧪 Optimizer Pro", 
        "📅 Vax Sentinel", "🩺 Health Triage", "🧬 Fertility Sentinel", 
        "♻️ Green Cycle Hub", "💊 Drug Safety", "⚙️ System Admin"
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
        if st.form_submit_button("COMMITTING DATA..."):
            gain = w_now - w_in
            adg = gain/days
            profit = (w_now * MARKET_DATABASE[sp]["price"]) - (feed * 60)
            st.session_state.db.append({
                "uid": f"AEG-{random.randint(1000,9999)}", "spec": sp, "sire": sire, 
                "adg": adg, "profit": profit, "weight": w_now, "feed": feed,
                "date": datetime.now().strftime("%Y-%m-%d"), "manure": days * MARKET_DATABASE[sp]["manure"]
            })
            st.rerun()

# ==========================================
# 4. MODULES
# ==========================================

# --- DASHBOARD & WEATHER ---
if nav == "📊 Tactical Dashboard":
    st.title("Tactical Herd Dashboard")
    weather = get_live_weather("Nakuru")
    if weather:
        c1, c2, c3 = st.columns(3)
        c1.metric("Live Temp", f"{weather['main']['temp']}°C")
        c2.metric("Humidity", f"{weather['main']['humidity']}%")
        c3.info(f"Alert: {'Rain Risk' if 'rain' in weather['weather'][0]['description'] else 'Clear Sky'}")
    
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.metric("Total Net Profit", f"KES {df['profit'].sum():,.0f}")
        st.dataframe(df, use_container_width=True)
    else: st.info("Registry empty.")


# --- SUGGESTION 3: THE FINANCIAL BURN RATE ---
def calculate_daily_burn(db):
    st.title("💸 Economic Velocity & Burn Rate")
    
    if not db:
        st.info("Log animal data to see financial velocity.")
        return

    df = pd.DataFrame(db)
    
    # Assumptions for logic
    avg_milk_price = 55 # KES per liter
    labor_cost_per_head = 20 # KES per day
    
    for index, row in df.iterrows():
        with st.expander(f"Financial Health: {row['uid']}"):
            # Daily Revenue from Growth (Weight Gain Value)
            daily_revenue = row['adg'] * MARKET_DATABASE[row['spec']]['price']
            
            # Daily Expenses (Feed + Labor)
            daily_expense = (row['feed'] / 15) * 60 + labor_cost_per_head # approx daily feed cost
            
            net_velocity = daily_revenue - daily_expense
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Daily Growth Value", f"KES {daily_revenue:.2f}")
            c2.metric("Daily Burn (Costs)", f"KES {daily_expense:.2f}", delta_color="inverse")
            
            if net_velocity > 0:
                c3.metric("Net Daily Margin", f"KES {net_velocity:.2f}", delta=f"{net_velocity:.2f}")
                st.success("✅ This asset is adding value to the farm.")
            else:
                c3.metric("Net Daily Margin", f"KES {net_velocity:.2f}", delta=f"{net_velocity:.2f}")
                st.error("🚨 BURN ALERT: This animal is costing more than it is growing. Review feed or genetics.")
# --- SIRE SCORECARD ---
elif nav == "🧬 Genetic Scorecard":
    st.title("Sire Genetic Merit Rankings")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        df['target'] = df['spec'].apply(lambda x: MARKET_DATABASE[x]['std_adg'])
        df['deviation'] = df['adg'] - df['target']
        rank = df.groupby('sire')['deviation'].mean().sort_values(ascending=False).reset_index()
        st.table(rank.style.background_gradient(cmap='RdYlGn'))
    else: st.warning("No breeding data available.")

# --- OPTIMIZER PRO ---
elif nav == "🧪 Optimizer Pro":
    st.title("Nutritional Feed Lab")
    
    t_cp = st.number_input("Target Protein %", 10.0, 30.0, 16.0)
    e_name = st.selectbox("Energy Ingredient", [k for k,v in FEED_LIBRARY.items() if v['type'] == 'Energy'])
    p_name = st.selectbox("Protein Ingredient", [k for k,v in FEED_LIBRARY.items() if v['type'] == 'Protein'])
    
    cp1, cp2 = FEED_LIBRARY[e_name]['cp'], FEED_LIBRARY[p_name]['cp']
    if cp1 < t_cp < cp2:
        parts_e = abs(cp2 - t_cp)
        parts_p = abs(cp1 - t_cp)
        total = parts_e + parts_p
        st.success(f"Mix: {(parts_e/total)*100:.1f}% {e_name} | {(parts_p/total)*100:.1f}% {p_name}")
    else: st.error("Target CP is impossible with these ingredients.")

# --- VAX SENTINEL ---
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

# --- HEALTH TRIAGE ---
elif nav == "🩺 Health Triage":
    st.title("Clinical Triage & Field Response")
    
    st.subheader("1. Vet Directory")
    reg = st.selectbox("Region", list(VET_DIRECTORY.keys()))
    st.write(VET_DIRECTORY[reg])
    
    st.subheader("2. Symptom Checker")
    sys = st.selectbox("Affected System", list(TRIAGE_MATRIX.keys()))
    sym = st.selectbox("Observed Sign", list(TRIAGE_MATRIX[sys].keys()))
    res = TRIAGE_MATRIX[sys][sym]
    st.error(f"**Level:** {res['risk']} | **Potential:** {res['diag']}")
    st.info(f"**Immediate Action:** {res['action']}")

# --- FERTILITY SENTINEL ---
elif nav == "🧬 Fertility Sentinel":
    st.title("Reproductive Cycle Predictor")
    
    spec = st.selectbox("Species", list(MARKET_DATABASE.keys()))
    last_h = st.date_input("Last Heat Date")
    st.metric("Next Heat Peak", (last_h + timedelta(days=MARKET_DATABASE[spec]['cycle'])).strftime("%d %b"))
    st.metric("Gestation Due Date", (last_h + timedelta(days=MARKET_DATABASE[spec]['gest'])).strftime("%d %b, %Y"))
    # --- SUGGESTION 2: FERTILITY GOLDEN HOUR ---
def fertility_golden_hour():
    st.subheader("🕒 The AI 'Golden Hour' Predictor")
    
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        observed_time = st.time_input("When did you first see Standing Heat?", datetime.now().time())
        observed_date = st.date_input("Date observed", datetime.now().date())
    
    # Combine date and time
    start_time = datetime.combine(observed_date, observed_time)
    
    # The Science: Best AI window is 6-12 hours after standing heat starts
    ai_window_start = start_time + timedelta(hours=6)
    ai_window_end = start_time + timedelta(hours=12)
    
    with col_t2:
        st.write("### 🎯 Best Insemination Window")
        st.warning(f"**Start AI From:** {ai_window_start.strftime('%I:%M %p')}")
        st.error(f"**Close Window By:** {ai_window_end.strftime('%I:%M %p')}")
        
        # Countdown logic
        time_diff = ai_window_start - datetime.now()
        if datetime.now() < ai_window_start:
            st.info(f"Wait {time_diff.seconds // 3600} hours before calling the technician.")
        elif ai_window_start <= datetime.now() <= ai_window_end:
            st.success("🚀 STATUS: OPTIMAL. Call your AI Technician NOW.")
        else:
            st.error("❌ STATUS: EXPIRED. You may have missed this cycle.")

# --- GREEN CYCLE ---
elif nav == "♻️ Green Cycle Hub":
    st.title("Circular Waste-to-Energy")
    
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        total_m = df['manure'].sum()
        st.metric("Total Manure Logged (kg)", f"{total_m:,.1f}")
        st.info(f"Current herd can generate **{total_m * 0.05:.2f} m³** of biogas per day.")
        # --- THE GENIUS SLURRY UPGRADE ---
def bio_slurry_logic(total_manure):
    st.subheader("🌱 Bio-Slurry Fertilizer Value")
    # 1kg manure produces approx 0.7L of high-quality slurry
    slurry_liters = total_manure * 0.7
    # Value of slurry vs 50kg bag of fertilizer (KES 3500)
    savings = (slurry_liters / 50) * 3500 
    
    st.metric("Organic Fertilizer Created", f"{slurry_liters:.1f} Liters")
    st.success(f"💰 This replaces KES {savings:,.0f} in synthetic fertilizer costs!")
        

# --- DRUG SAFETY ---
elif nav == "💊 Drug Safety":
    st.title("Withdrawal Safety Tracker")
    drug = st.selectbox("Administered Drug", list(MEDICATION_WITHDRAWAL.keys()))
    d_given = st.date_input("Date Administered")
    m_safe = d_given + timedelta(days=MEDICATION_WITHDRAWAL[drug]['milk'])
    t_safe = d_given + timedelta(days=MEDICATION_WITHDRAWAL[drug]['meat'])
    st.warning(f"**Safe for Milk:** {m_safe} | **Safe for Meat:** {t_safe}")
    if datetime.now().date() < m_safe: st.error("🚫 MILK IS CURRENTLY UNSAFE FOR HUMAN CONSUMPTION.")

# --- SYSTEM ADMIN ---
elif nav == "⚙️ System Admin":
    st.title("Admin & Cloud Snapshots")
    if st.button("Generate Cloud Backup Code"):
        st.code(base64.b64encode(json.dumps(st.session_state.db).encode()).decode())
    if st.button("PURGE ALL DATA"):
        st.session_state.db = []
        st.rerun()

st.divider()
st.caption(f"AEGIS v21.0 | Eric Kamau | University of Nairobi | {datetime.now().year}")
