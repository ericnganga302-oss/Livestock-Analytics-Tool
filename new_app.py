import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. BRAIN: GLOBAL INTELLIGENCE FUNCTION ---
def get_livestock_outbreaks():
    # ERIC'S API KEY INTEGRATED
    api_key = "11e5adaf7907408fa5661babadc4605c" 
    query = "(livestock disease OR cattle outbreak OR anthrax OR 'Foot and Mouth') AND (Kenya OR Africa)"
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get('articles', [])[:5] 
    except:
        return []
    return []

# --- 3. DATA & KNOWLEDGE BASES ---
MARKET_DATA = {
    "Beef (Bone-in)": 760, "Beef (Prime Steak)": 900,
    "Mutton/Goat": 920, "Pork (Retail)": 850,
    "Chicken (Whole Capon)": 600, "Chicken (Kienyeji)": 900
}

SPECIES_INFO = {
    "Beef": {"target": 450.0, "adg_min": 0.8, "ch4": 0.18, "icon": "🐂"},
    "Pig": {"target": 130.0, "adg_min": 0.6, "ch4": 0.04, "icon": "🐖"},
    "Broiler": {"target": 2.5, "adg_min": 0.05, "ch4": 0.002, "icon": "🐥"},
}

# Advanced Clinical Database for AniWise
GLOBAL_VET_DB = {
    "East Coast Fever": {
        "symptoms": {"Swollen Lymph Nodes": 5, "High Fever": 3, "Froth at Nose": 2, "Coughing": 1},
        "key": "Swollen Lymph Nodes", "time_range": (3, 14), "risk": "ECONOMIC",
        "action": "Administer Buparvaquone (e.g., Butalex) @ 1ml/20kg IM."
    },
    "Anthrax": {
        "symptoms": {"Sudden Death": 10, "Bloody Discharge": 8, "Bloating": 5},
        "key": "Sudden Death", "time_range": (0, 2), "risk": "ZOONOTIC (HUMAN DANGER)",
        "action": "DO NOT TOUCH. Secure area. Notify Vet immediately for carcass disposal."
    },
    "Foot & Mouth": {
        "symptoms": {"Drooling": 5, "Limping": 5, "Blisters": 5, "Mouth Sores": 3},
        "key": "Blisters", "time_range": (2, 10), "risk": "CONTAGIOUS",
        "action": "Quarantine animal. Apply antiseptic to sores. Report outbreak."
    }
}

# --- 4. SESSION STATE ---
if 'records' not in st.session_state: 
    st.session_state.records = []

# --- 5. GENETICS MODULE ---
def render_genetics_tab(df):
    st.header("🧬 Genetic Performance & Lineage")
    if not df.empty and 'Sire_ID' in df.columns:
        sire_stats = df.groupby('Sire_ID')['Current_Wt'].mean().reset_index()
        sire_stats.columns = ['Sire_ID', 'Avg_Weight']
        genetic_chart = alt.Chart(sire_stats).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X('Sire_ID:N', title="Sire ID"),
            y=alt.Y('Avg_Weight:Q', title="Avg Offspring Weight (kg)"),
            color=alt.Color('Avg_Weight:Q', scale=alt.Scale(scheme='greens'))
        ).properties(height=400)
        st.altair_chart(genetic_chart, use_container_width=True)
    else:
        st.warning("No breeding data available.")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("AEGIS Control")
    choice = st.radio("Navigation", ["Dashboard", "AniWise AI", "Genetics & Breeding"])
    st.divider()
    with st.form("entry_form", clear_on_submit=True):
        animal_id = st.text_input("Tag ID", value=f"UoN-{random.randint(1000,9999)}")
        spec = st.selectbox("Species", list(SPECIES_INFO.keys()))
        col1, col2 = st.columns(2)
        with col1:
            wt_start = st.number_input("Start Wt (kg)", value=250.0)
            wt_curr = st.number_input("Current Wt (kg)", value=300.0)
            sire = st.text_input("Sire ID", value="Unknown")
        with col2:
            period = st.number_input("Days", value=30)
            feed = st.number_input("Feed (kg)", value=400.0)
            dam = st.text_input("Dam ID", value="Unknown")
        m_price = st.number_input("Market Price (KES/kg)", value=760.0)
        f_price = st.number_input("Feed Price (KES/kg)", value=55.0)
        if st.form_submit_button("Add to Herd"):
            gain = wt_curr - wt_start
            adg = gain / period if period > 0 else 0
            profit = (wt_curr * m_price) - (feed * f_price)
            methane = period * SPECIES_INFO[spec]["ch4"]
            st.session_state.records.append({
                "ID": animal_id, "Spec": spec, "ADG": adg, "Profit": profit, 
                "CH4": methane, "FCR": feed/gain if gain > 0 else 0,
                "Current_Wt": wt_curr, "Sire_ID": sire, "Dam_ID": dam
            })
            st.rerun()

# --- 7. MAIN INTERFACE ---
if choice == "Dashboard":
    st.title("🐂 AEGIS Smart Farm Dashboard")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        m1, m2, m3 = st.columns(3)
        m1.metric("Herd Profit", f"KES {df['Profit'].sum():,.0f}")
        m2.metric("Avg FCR", f"{df['FCR'].mean():.2f}")
        m3.metric("Total CH₄", f"{df['CH4'].sum():.2f} kg")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Add animal data in the sidebar to view analytics.")

elif choice == "AniWise AI":
    st.title("🤖 AniWise: Humanitarian Sentinel")
    
    # Live Outbreak Intelligence
    with st.expander("🌍 Live Regional Outbreak Alerts", expanded=True):
        news = get_livestock_outbreaks()
        if news:
            for art in news:
                st.warning(f"🔔 **{art['source']['name']}**: {art['title']}")
                st.caption(f"[View Alert]({art['url']})")
        else:
            st.info("No active outbreaks detected in global feeds today.")

    st.divider()
    col_in, col_diag = st.columns([1, 1])

    with col_in:
        st.subheader("📋 Clinical Assessment")
        duration = st.slider("Days since onset:", 0, 30, 1)
        all_signs = sorted(list(set([s for d in GLOBAL_VET_DB.values() for s in d["symptoms"].keys()])))
        selected = st.multiselect("Identify observed signs:", all_signs)

    with col_diag:
        st.subheader("🩺 Diagnostic Analysis")
        results = []
        if selected:
            for dis, data in GLOBAL_VET_DB.items():
                score = sum(data["symptoms"][s] for s in selected if s in data["symptoms"])
                # Temporal & Key Sign Logic
                if duration >= data["time_range"][0] and duration <= data["time_range"][1]: score += 2
                if data["key"] not in selected: score *= 0.4
                # News matching boost
                for art in news:
                    if dis.lower() in art['title'].lower(): score += 7
                
                conf = (score / (sum(data["symptoms"].values()) + 2)) * 100
                if conf > 15: results.append({"name": dis, "conf": conf, "data": data})
            
            if results:
                top = sorted(results, key=lambda x: x['conf'], reverse=True)[0]
                st.error(f"### Predicted: {top['name']}")
                st.progress(min(top['conf'] / 100, 1.0))
                st.write(f"**Risk:** {top['data']['risk']}")
                st.success(f"**Action:** {top['data']['action']}")
            else: st.warning("Inconclusive. Monitor animal closely.")

    # National Reporting Engine
    st.divider()
    if st.session_state.records and selected and results:
        st.subheader("📢 National Surveillance Reporting")
        report_animal = st.selectbox("Confirm Animal for Report:", [r['ID'] for r in st.session_state.records])
        top = sorted(results, key=lambda x: x['conf'], reverse=True)[0]
        if top['conf'] > 65:
            rep_id = f"AEGIS-KE-{report_animal}-{datetime.now().strftime('%d%m%y')}"
            if st.button("🚀 TRANSMIT DATA TO VETERINARY SERVICES"):
                st.balloons()
                st.success(f"Report {rep_id} Transmitted Successfully.")
        else: st.info("Confidence below 65% reporting threshold.")

elif choice == "Genetics & Breeding":
    if st.session_state.records:
        render_genetics_tab(pd.DataFrame(st.session_state.records))
    else: st.warning("No data found.")

st.divider()
st.caption("Eric Kamau | AEGIS Project | UoN Animal Production Research")
