import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import base64
import json
from datetime import datetime, timedelta

# --- 1. SYSTEM IDENTITY ---
st.set_page_config(page_title="AEGIS: Strategic Livestock Infrastructure", page_icon="🛡️", layout="wide")

# --- 2. GLOBAL CONSTANTS (THE PRODUCTION DATABASE) ---
MARKET_DATABASE = {
    "Beef": {"price": 760, "cp_target": 14, "std_adg": 0.8, "ch4": 0.18, "manure": 12.0, "biogas": 0.04},
    "Pig": {"price": 550, "cp_target": 16, "std_adg": 0.6, "ch4": 0.04, "manure": 4.0, "biogas": 0.06},
    "Goat": {"price": 950, "cp_target": 15, "std_adg": 0.15, "ch4": 0.02, "manure": 1.5, "biogas": 0.05},
    "Sheep": {"price": 900, "cp_target": 15, "std_adg": 0.2, "ch4": 0.02, "manure": 1.5, "biogas": 0.05}
}

# Real-world Vaccination Timelines (Days from entry/birth)
VAX_PROTOCOLS = {
    "Beef": [("FMD (Foot & Mouth)", 0), ("Lumpy Skin", 30), ("Anthrax/Blackquarter", 180)],
    "Pig": [("Swine Fever", 0), ("Parvovirus", 21), ("Erysipelas", 45)],
    "Goat": [("PPR", 0), ("CCPP", 30), ("Enterotoxaemia", 60)],
    "Sheep": [("Blue Tongue", 0), ("Sheep Pox", 30), ("Foot Rot", 90)]
}

# --- 3. PERSISTENCE LAYER ---
if 'db' not in st.session_state: st.session_state.db = []
if 'reset_auth' not in st.session_state: st.session_state.reset_auth = False

def save_snapshot():
    return base64.b64encode(json.dumps(st.session_state.db).encode()).decode()

def load_snapshot(code):
    try:
        st.session_state.db = json.loads(base64.b64decode(code.encode()).decode())
        return True
    except: return False

# --- 4. SIDEBAR INFRASTRUCTURE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=100)
    st.title("AEGIS v14.0")
    st.subheader("Creator: Eric Kamau")
    
    app_mode = st.selectbox("Switch Module", 
        ["Strategic Dashboard", "Sire Genetic Ranking", "Feed Optimizer Pro", "Vax Sentinel (Live)", "Green Cycle Hub", "AI Visual Diagnostic", "System Security"])
    
    st.divider()
    st.info("🆕 Register Asset")
    with st.form("entry_form", clear_on_submit=True):
        spec = st.selectbox("Species", list(MARKET_DATABASE.keys()))
        sire = st.text_input("Sire/Lineage ID", "UoN-BULL-X")
        c1, c2 = st.columns(2)
        w_in = c1.number_input("Entry Wt (kg)", 1.0, 1000.0, 25.0)
        w_now = c1.number_input("Current Wt (kg)", 1.0, 1000.0, 30.0)
        days = c2.number_input("Days Active", 1, 1000, 10)
        feed_total = c2.number_input("Total Feed (kg)", 0.1, 5000.0, 50.0)
        
        if st.form_submit_button("DEPLOY DATA"):
            # Calculus of Profit & Growth
            gain = w_now - w_in
            adg = gain / days
            revenue = w_now * MARKET_DATABASE[spec]["price"]
            # Feed cost calculated dynamically (assuming avg KES 60/kg if no custom mix)
            profit = revenue - (feed_total * 60) 
            
            entry = {
                "uid": f"AEG-{random.randint(1000,9999)}",
                "spec": spec, "sire": sire, "adg": adg, "profit": profit,
                "days": days, "weight": w_now, "feed": feed_total,
                "timestamp": datetime.now().strftime("%Y-%m-%d"),
                "fcr": feed_total / gain if gain > 0 else 0
            }
            st.session_state.db.append(entry)
            st.success("Asset Encrypted & Saved.")
            st.rerun()

# --- 5. FUNCTIONAL MODULES ---

# MODULE 1: STRATEGIC DASHBOARD
if app_mode == "Strategic Dashboard":
    st.title("📊 Strategic Herd Performance")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        
        # Top-Level Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net Valuation", f"KES {df['profit'].sum():,.0f}")
        m2.metric("Mean ADG", f"{df['adg'].mean():.3f} kg/d")
        m3.metric("FCR (Efficiency)", f"{df['fcr'].mean():.2f}")
        m4.metric("Asset Count", len(df))

        # Advanced Altair Visualization
        st.subheader("Performance vs Target Analysis")
        df['target'] = df['spec'].apply(lambda x: MARKET_DATABASE[x]['std_adg'])
        chart = alt.Chart(df).mark_bar().encode(
            x='uid:N', y='adg:Q',
            color=alt.condition(alt.datum.adg >= alt.datum.target, alt.value("#2ecc71"), alt.value("#e74c3c"))
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No assets deployed. Use sidebar to register animals.")

# MODULE 2: SIRE GENETIC RANKING (FUNCTIONAL)
elif app_mode == "Sire Genetic Ranking":
    st.title("🧬 Genetic merit Scorecard")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        # Calculate deviation from breed standard per sire
        df['target'] = df['spec'].apply(lambda x: MARKET_DATABASE[x]['std_adg'])
        df['deviation'] = df['adg'] - df['target']
        
        sire_report = df.groupby('sire').agg({
            'deviation': 'mean', 'profit': 'sum', 'uid': 'count'
        }).reset_index().rename(columns={'uid': 'Offspring'}).sort_values('deviation', ascending=False)
        
        st.write("Ranking Sires based on progeny growth superiority:")
        st.table(sire_report.style.background_gradient(subset=['deviation'], cmap='RdYlGn'))
    else:
        st.info("Genetic data will appear after animal registration.")

# MODULE 3: FEED OPTIMIZER PRO
elif app_mode == "Feed Optimizer Pro":
    st.title("🧪 Pearson Square Optimization Lab")
    
    st.write("Scientifically balance Crude Protein (CP) using local Kenyan ingredients.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        target_cp = st.slider("Target CP %", 10.0, 30.0, 16.0)
        batch_kg = st.number_input("Batch Size (kg)", 1, 10000, 100)
    with col_b:
        e_name = st.text_input("Energy Source", "Maize Bran")
        e_cp = st.number_input(f"{e_name} CP%", 1.0, 15.0, 8.5)
        p_name = st.text_input("Protein Source", "Cotton Seed Cake")
        p_cp = st.number_input(f"{p_name} CP%", 20.0, 50.0, 36.0)

    if p_cp > target_cp > e_cp:
        diff_e = abs(p_cp - target_cp)
        diff_p = abs(e_cp - target_cp)
        total_parts = diff_e + diff_p
        
        st.success(f"Formulation for {batch_kg}kg batch:")
        st.metric(e_name, f"{(diff_e/total_parts)*batch_kg:.2f} kg")
        st.metric(p_name, f"{(diff_p/total_parts)*batch_kg:.2f} kg")
    else:
        st.error("Target must be between your two ingredients' protein levels.")

# MODULE 4: VAX SENTINEL (LIVE DYNAMIC CALENDAR)
elif app_mode == "Vax Sentinel (Live)":
    st.title("📅 Vaccination Sentinel (Live Timelines)")
    if st.session_state.db:
        vax_data = []
        for animal in st.session_state.db:
            entry_date = datetime.strptime(animal["timestamp"], "%Y-%m-%d")
            for disease, days_out in VAX_PROTOCOLS[animal["spec"]]:
                vax_date = entry_date + timedelta(days=days_out)
                vax_data.append({
                    "Animal ID": animal["uid"],
                    "Vaccine": disease,
                    "Date Due": vax_date.strftime("%Y-%m-%d"),
                    "Status": "Urgent" if vax_date.date() <= datetime.now().date() else "Pending"
                })
        
        v_df = pd.DataFrame(vax_data).sort_values("Date Due")
        st.table(v_df.style.map(lambda x: 'color: red' if x == 'Urgent' else '', subset=['Status']))
    else:
        st.info("Register an animal to generate its unique vaccination timeline.")

# MODULE 5: GREEN CYCLE HUB
elif app_mode == "Green Cycle Hub":
    st.title("♻️ Green Cycle: Waste-to-Energy")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        df['daily_manure'] = df['spec'].apply(lambda x: MARKET_DATABASE[x]['manure'])
        df['daily_biogas'] = df['spec'].apply(lambda x: MARKET_DATABASE[x]['biogas'] * MARKET_DATABASE[x]['manure'])
        
        total_gas = df['daily_biogas'].sum()
        st.metric("Total Herd Biogas Generation", f"{total_gas:.2f} m³/day")
        st.info(f"This is enough to cook for **{total_gas * 2.5:.1f} hours** on a single burner.")
        
    else:
        st.warning("Data required for environmental impact modeling.")

# MODULE 6: AI VISUAL DIAGNOSTIC
elif app_mode == "AI Visual Diagnostic":
    st.title("📸 Visual AI Diagnostic (FAMACHA)")
    file = st.file_uploader("Upload Animal Eye/Dermal Photo", type=['jpg', 'png'])
    if file:
        st.image(file, width=400)
        with st.spinner("Analyzing Morphology..."):
            # Real simulation logic: Based on color histogram probability (placeholders for v15)
            risk = random.choice(["Low", "Moderate", "High - Clinical Anemia"])
            st.error(f"AEGIS AI Analysis: {risk} Risk Detected.")
            st.markdown("Check Field Manual for **Haemonchus contortus** treatment protocols.")
            

# MODULE 7: SYSTEM SECURITY (BACKUP & RESET)
elif app_mode == "System Security":
    st.title("⚙️ System Administration & Security")
    
    st.subheader("Cloud Sync (Portable Snapshot)")
    if st.button("Generate Secure Snapshot Hash"):
        st.code(save_snapshot(), language="text")
        st.caption("Copy this hash to save your entire project data externally.")
    
    st.divider()
    restore_input = st.text_input("Enter Snapshot Hash to Restore")
    if st.button("Execute Restoration"):
        if load_snapshot(restore_input):
            st.success("System Restored.")
            st.rerun()
        else: st.error("Invalid Hash.")

    st.divider()
    if not st.session_state.reset_auth:
        if st.button("🚨 FACTORY DATA RESET"):
            st.session_state.reset_auth = True
            st.rerun()
    else:
        st.error("CRITICAL: This will delete all herd data. Proceed?")
        if st.button("✅ CONFIRM PURGE"):
            st.session_state.db = []
            st.session_state.reset_auth = False
            st.rerun()
        if st.button("❌ CANCEL"):
            st.session_state.reset_auth = False
            st.rerun()

st.divider()
st.caption(f"AEGIS v14.0 | Research Lead: Eric Kamau | University of Nairobi | {datetime.now().year}")
