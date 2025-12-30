import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import urllib.parse 
from datetime import datetime, timedelta

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. DATA ARCHITECTURE (The Knowledge Core) ---
MARKET_DATA = {
    "Beef (Bone-in)": 760, "Beef (Prime Steak)": 900,
    "Mutton/Goat": 920, "Pork (Retail)": 850,
    "Chicken (Whole Capon)": 600, "Chicken (Kienyeji)": 900
}

SPECIES_INFO = {
    "Beef": {"target": 450.0, "ch4": 0.18, "manure": 12.0, "biogas": 0.04, "vax": [("Lumpy Skin", 0), ("Foot & Mouth", 14), ("Anthrax", 30)]}, 
    "Pig": {"target": 130.0, "ch4": 0.04, "manure": 4.0, "biogas": 0.06, "vax": [("Swine Fever", 0), ("Parvovirus", 21), ("Erysipelas", 45)]},
    "Broiler": {"target": 2.5, "ch4": 0.002, "manure": 0.1, "biogas": 0.08, "vax": [("Newcastle", 7), ("Gumboro", 14), ("Fowl Pox", 21)]},
}

GLOBAL_VET_DB = {
    "East Coast Fever": {"symptoms": ["Swollen Lymph Nodes", "High Fever", "Froth at Nose", "Coughing"], "key": "Swollen Lymph Nodes", "time": (3, 14), "risk": "ECONOMIC", "act": "Administer Buparvaquone IM."},
    "Anthrax": {"symptoms": ["Sudden Death", "Bloody Discharge", "Bloating"], "key": "Sudden Death", "time": (0, 2), "risk": "ZOONOTIC (DANGER)", "act": "DO NOT TOUCH. Notify Authorities."},
    "Foot & Mouth": {"symptoms": ["Drooling", "Limping", "Blisters", "Mouth Sores"], "key": "Blisters", "time": (2, 10), "risk": "CONTAGIOUS", "act": "Quarantine & apply antiseptics."}
}

# --- 3. SESSION STATE ---
if 'records' not in st.session_state: st.session_state.records = []

# --- 4. API & UTILITIES ---
@st.cache_data(ttl=3600)
def get_outbreaks():
    api_key = "11e5adaf7907408fa5661babadc4605c"
    url = f"https://newsapi.org/v2/everything?q=(livestock disease OR anthrax) AND Kenya&apiKey={api_key}"
    try:
        r = requests.get(url, timeout=3)
        return r.json().get('articles', [])[:3] if r.status_code == 200 else []
    except: return []

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("AEGIS v6.0")
    choice = st.radio("Navigation", ["Dashboard", "AniWise AI", "Vax Calendar", "Genetics", "Feed & Profit Lab", "Field Manual"])
    
    st.divider()
    with st.expander("📝 New Animal Entry", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            a_id = st.text_input("Tag ID", value=f"UoN-{random.randint(1000,9999)}")
            a_spec = st.selectbox("Species", list(SPECIES_INFO.keys()))
            col_a, col_b = st.columns(2)
            with col_a:
                w_s = st.number_input("Start Wt", 250.0)
                w_c = st.number_input("Current Wt", 300.0)
            with col_b:
                days = st.number_input("Days", 30)
                feed = st.number_input("Feed (kg)", 400.0)
            sire = st.text_input("Sire ID", "Unknown")
            dam = st.text_input("Dam ID", "Unknown")
            if st.form_submit_button("Add to Herd"):
                gain = w_c - w_s
                st.session_state.records.append({
                    "ID": a_id, "Spec": a_spec, "ADG": gain/days if days > 0 else 0,
                    "Profit": (w_c * 760) - (feed * 55), "CH4": days * SPECIES_INFO[a_spec]["ch4"],
                    "Biogas": (days * SPECIES_INFO[a_spec]["manure"]) * SPECIES_INFO[a_spec]["biogas"],
                    "Date": datetime.now().strftime("%Y-%m-%d"), "Current_Wt": w_c, "Sire_ID": sire, "Dam_ID": dam
                })
                st.rerun()

# --- 6. NAVIGATION LOGIC ---

# A. DASHBOARD
if choice == "Dashboard":
    st.title("🐂 AEGIS Smart Farm Dashboard")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Profit", f"KES {df['Profit'].sum():,.0f}")
        m2.metric("Methane", f"{df['CH4'].sum():.1f} kg")
        m3.metric("Biogas", f"{df['Biogas'].sum():.1f} m³")
        m4.metric("Trees Needed", int(df['CH4'].sum()))
        
        st.subheader("♻️ Green Cycle Analytics")
        st.altair_chart(alt.Chart(df).mark_bar().encode(x='ID', y='Biogas', color='Spec'), use_container_width=True)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Export Herd Data (CSV)", df.to_csv(index=False), "aegis_data.csv", "text/csv")
    else: st.info("Welcome, Eric. Add animal data in the sidebar to begin.")

# B. ANIWISE AI (Diagnostic Sentinel)
elif choice == "AniWise AI":
    st.title("🤖 AniWise AI Diagnostic")
    news = get_outbreaks()
    results = []
    
    with st.expander("🌍 Live Regional Alerts"):
        for n in news: st.warning(f"🔔 {n['title']}")
            
    c_in, c_out = st.columns(2)
    with c_in:
        obs = st.multiselect("Select Signs:", ["Swollen Lymph Nodes", "High Fever", "Froth at Nose", "Coughing", "Sudden Death", "Bloody Discharge", "Drooling", "Limping", "Blisters"])
        dur = st.slider("Days Sick:", 0, 30, 1)
        
    with c_out:
        if obs:
            for d, data in GLOBAL_VET_DB.items():
                score = sum(2 for s in obs if s in data["symptoms"])
                if data["key"] in obs: score += 5
                if data["time"][0] <= dur <= data["time"][1]: score += 2
                conf = (score / 15) * 100
                if conf > 20: results.append({"name": d, "conf": conf, "risk": data["risk"], "act": data["act"]})
            
            if results:
                top = sorted(results, key=lambda x: x['conf'], reverse=True)[0]
                st.error(f"### {top['name']} ({int(top['conf'])}%)")
                st.write(f"**Risk:** {top['risk']}\n\n**Action:** {top['act']}")
                if st.button("Transmit to Ministry"): st.success("Report Sent.")
            else: st.warning("Data inconclusive.")

# C. VACCINATION CALENDAR (The New Feature)
elif choice == "Vax Calendar":
    st.title("📅 Vaccination Sentinel")
    
    if st.session_state.records:
        vax_list = []
        for r in st.session_state.records:
            entry_date = datetime.strptime(r["Date"], "%Y-%m-%d")
            for v_name, v_days in SPECIES_INFO[r["Spec"]]["vax"]:
                due = entry_date + timedelta(days=v_days)
                vax_list.append({"Animal": r["ID"], "Species": r["Spec"], "Vaccine": v_name, "Due Date": due.strftime("%Y-%m-%d"), "Status": "⏳ Pending"})
        
        vax_df = pd.DataFrame(vax_list)
        st.table(vax_df)
        st.info("💡 Tip: Vaccinate only healthy animals. Store vaccines between 2°C and 8°C.")
    else: st.warning("No animals found in herd.")

# D. GENETICS
elif choice == "Genetics":
    st.title("🧬 Breeding Intelligence")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        sire_df = df.groupby('Sire_ID')['Current_Wt'].mean().reset_index()
        st.altair_chart(alt.Chart(sire_df).mark_bar().encode(x='Sire_ID', y='Current_Wt'), use_container_width=True)
    else: st.info("Add Sire/Dam data to track performance.")

# E. FEED & PROFIT LAB
elif choice == "Feed & Profit Lab":
    st.title("🧪 The AEGIS Lab")
    t1, t2 = st.tabs(["Pearson Square Feed Mix", "Profit Simulator"])
    with t1:
        target = st.number_input("Target Protein %", 16)
        i1_p = st.number_input("Base Protein % (e.g. Bran)", 8)
        i2_p = st.number_input("Concentrate Protein % (e.g. Cake)", 36)
        if i2_p > target > i1_p:
            p1, p2 = abs(i2_p-target), abs(i1_p-target)
            st.success(f"Mix: {(p1/(p1+p2))*100:.1f}% Base with {(p2/(p1+p2))*100:.1f}% Concentrate")
    with t2:
        count = st.number_input("Heads", 10)
        costs = st.number_input("Total Costs/Head", 30000)
        rev = st.number_input("Expected Sale/Head", 50000)
        st.metric("ROI", f"{((rev-costs)/costs)*100:.1f}%")

# F. FIELD MANUAL
elif choice == "Field Manual":
    st.title("📚 Field Emergency Manual")
    
    with st.expander("Clinical Exam 101"):
        st.write("1. Check Muzzle (Dry = Fever). 2. Check Eyes (Pale = Worms). 3. Check Breath (Acetone smell = Ketosis).")
    with st.expander("Weight by Tape"):
        st.write("Weight (kg) = (Girth cm)² x Length cm / 10838")

st.divider()
st.caption("Eric Kamau | AEGIS | University of Nairobi | Humanity-First Livestock Intelligence")
