import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import urllib.parse 
import base64
import json
from datetime import datetime, timedelta

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. VALIDATED DATA CORE ---
MARKET_DATA = {"Beef": 760, "Pig": 550, "Goat": 950, "Sheep": 900, "Poultry": 600}

SPECIES_INFO = {
    "Beef": {"ch4": 0.18, "manure": 12.0, "biogas": 0.04, "feed_price": 55, "std_adg": 0.8, "vax": [("FMD", 0), ("LSD", 30), ("Anthrax", 180)]}, 
    "Pig": {"ch4": 0.04, "manure": 4.0, "biogas": 0.06, "feed_price": 65, "std_adg": 0.6, "vax": [("CSF", 0), ("Parvo", 21), ("Erysipelas", 45)]},
    "Goat": {"ch4": 0.02, "manure": 1.5, "biogas": 0.05, "feed_price": 45, "std_adg": 0.15, "vax": [("PPR", 0), ("Entero", 21), ("CCPP", 60)]},
    "Sheep": {"ch4": 0.02, "manure": 1.5, "biogas": 0.05, "feed_price": 45, "std_adg": 0.2, "vax": [("Blue Tongue", 0), ("Sheep Pox", 30)]}
}

# --- 3. CORE LOGIC ENGINES ---
def create_snapshot(data):
    return base64.b64encode(json.dumps(data).encode()).decode()

def load_snapshot(b64_str):
    try: return json.loads(base64.b64decode(b64_str.encode()).decode())
    except: return None

@st.cache_data(ttl=3600)
def get_outbreaks():
    api_key = "11e5adaf7907408fa5661babadc4605c"
    url = f"https://newsapi.org/v2/everything?q=livestock disease Kenya&apiKey={api_key}"
    try:
        r = requests.get(url, timeout=3)
        return r.json().get('articles', [])[:3] if r.status_code == 200 else []
    except: return []

# --- 4. SESSION MANAGEMENT ---
if 'records' not in st.session_state: st.session_state.records = []
if 'confirm' not in st.session_state: st.session_state.confirm = False

# --- 5. SIDEBAR COMMAND CENTER ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("AEGIS v9.0")
    nav = st.radio("Navigation", ["Dashboard", "ADG Analytics", "AniWise AI", "Vax Sentinel", "Field Manual"])
    
    st.divider()
    with st.expander("📝 Entry Terminal", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            sp = st.selectbox("Species", list(SPECIES_INFO.keys()))
            tid = f"AEG-{sp[:3].upper()}-{datetime.now().year}-{random.randint(100,999)}"
            c1, c2 = st.columns(2)
            w_s = c1.number_input("Start Wt (kg)", 1.0, 1000.0, 25.0)
            w_c = c1.number_input("Current Wt (kg)", 1.0, 1000.0, 30.0)
            days = c2.number_input("Days on Farm", 1, 5000, 10)
            feed = c2.number_input("Total Feed (kg)", 0.1, 10000.0, 50.0)
            sire = st.text_input("Sire/Lineage", "N/A")
            
            if st.form_submit_button("Commit Data"):
                # Precision Math
                adg = (w_c - w_s) / days
                profit = (w_c * MARKET_DATA[sp]) - (feed * SPECIES_INFO[sp]["feed_price"])
                st.session_state.records.append({
                    "ID": tid, "Spec": sp, "ADG": adg, "Profit": profit,
                    "CH4": days * SPECIES_INFO[sp]["ch4"], "Sire": sire,
                    "Biogas": (days * SPECIES_INFO[sp]["manure"]) * SPECIES_INFO[sp]["biogas"],
                    "Date": datetime.now().strftime("%Y-%m-%d"), "Weight": w_c,
                    "FCR": feed / (w_c - w_s) if (w_c - w_s) > 0 else 0
                })
                st.rerun()

    with st.expander("💾 Sync & Reset"):
        if st.button("Generate Snapshot"):
            st.code(create_snapshot(st.session_state.records))
        restore = st.text_input("Restore Code:")
        if st.button("Load"):
            data = load_snapshot(restore)
            if data: st.session_state.records = data; st.rerun()
        
        st.divider()
        if not st.session_state.confirm:
            if st.button("🗑️ Reset System"): st.session_state.confirm = True; st.rerun()
        else:
            if st.button("⚠️ CONFIRM PURGE"): st.session_state.records = []; st.session_state.confirm = False; st.rerun()
            if st.button("CANCEL"): st.session_state.confirm = False; st.rerun()

# --- 6. INTERFACE MODULES ---

if nav == "Dashboard":
    st.title("📊 Strategic Herd Overview")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net Profit", f"KES {df['Profit'].sum():,.0f}")
        m2.metric("Biogas Potential", f"{df['Biogas'].sum():.2f} m³")
        m3.metric("CH4 Footprint", f"{df['CH4'].sum():.2f} kg")
        m4.metric("Avg FCR", f"{df['FCR'].mean():.2f}")
        st.dataframe(df.style.highlight_max(axis=0, subset=['ADG', 'Profit']), use_container_width=True)
    else: st.info("System Ready. Awaiting initial entry...")

elif nav == "ADG Analytics":
    st.title("📈 Performance Intelligence")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        df['Std'] = df['Spec'].apply(lambda x: SPECIES_INFO[x]['std_adg'])
        df['Status'] = df.apply(lambda x: 'Above Standard' if x['ADG'] >= x['Std'] else 'Below Standard', axis=1)

        # Comparative Analytics Chart
        base = alt.Chart(df).encode(x='ID:N')
        bar = base.mark_bar().encode(
            y=alt.Y('ADG:Q', title='Actual ADG (kg/day)'),
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Above Standard', 'Below Standard'], range=['#2ecc71', '#e74c3c']))
        )
        line = base.mark_tick(color='blue', size=40).encode(y='Std:Q')
        
        st.altair_chart((bar + line).properties(height=400), use_container_width=True)
        st.caption("Blue ticks represent Breed Standards. Bars represent actual performance.")

        col_l, col_r = st.columns(2)
        col_l.subheader("Top Performers (Genetic)")
        col_l.table(df.sort_values('ADG', ascending=False)[['ID', 'Sire', 'ADG']].head(5))
        
        col_r.subheader("Species Efficiency")
        spec_avg = df.groupby('Spec')[['ADG', 'FCR']].mean()
        col_r.write(spec_avg)
    else: st.warning("Data required for analytics.")

elif nav == "Vax Sentinel":
    st.title("📅 Proactive Health Schedule")
    if st.session_state.records:
        v_tasks = []
        for r in st.session_state.records:
            base_d = datetime.strptime(r["Date"], "%Y-%m-%d")
            for name, delta in SPECIES_INFO[r["Spec"]]["vax"]:
                v_tasks.append({
                    "Animal ID": r["ID"], "Vaccine": name, 
                    "Due Date": (base_d + timedelta(days=delta)).strftime("%Y-%m-%d"),
                    "Target Species": r["Spec"]
                })
        st.table(pd.DataFrame(v_tasks).sort_values("Due Date"))
    else: st.info("Enter animals to generate schedule.")

elif nav == "Field Manual":
    st.title("📚 AEGIS Veterinary Protocol")
    tab1, tab2 = st.tabs(["Diagnostics", "Breed Standards"])
    with tab1:
        st.markdown("""
        ### 🩺 Clinical Triage SOP
        1. **Muzzle Check:** Dryness is the first sign of fever (>39.5°C).
        2. **Rumen Motility:** Fist in left paralumbar fossa. Normal = 2-3 waves per 2 mins.
        3. **Hydration:** Skin tenting >3 secs indicates severe dehydration.
        """)
        
    with tab2:
        st.write("Standards based on University of Nairobi Research Benchmarks:")
        st.json({k: f"{v['std_adg']} kg/day" for k, v in SPECIES_INFO.items()})

elif nav == "AniWise AI":
    st.title("🤖 AniWise AI")
    st.write("Real-time Outbreak Surveillance Active.")
    for o in get_outbreaks(): st.warning(f"🚨 ALERT: {o['title']}")

st.divider()
st.caption(f"Eric Kamau | AEGIS Project | Creator & Lead Developer | {datetime.now().year}")
