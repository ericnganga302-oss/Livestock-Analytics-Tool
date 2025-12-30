import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import urllib.parse 
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. BRAIN: GLOBAL INTELLIGENCE ---
@st.cache_data(ttl=3600) # Cache data for 1 hour to prevent API spam & speed up app
def get_livestock_outbreaks():
    api_key = "11e5adaf7907408fa5661babadc4605c" 
    query = "(livestock disease OR cattle outbreak OR anthrax OR 'Foot and Mouth') AND (Kenya OR Africa)"
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return response.json().get('articles', [])[:3] 
    except:
        return [] # Fail silently if no internet
    return []

# --- 3. DATA & KNOWLEDGE BASES ---
MARKET_DATA = {
    "Beef (Bone-in)": 760, "Beef (Prime Steak)": 900,
    "Mutton/Goat": 920, "Pork (Retail)": 850,
    "Chicken (Whole Capon)": 600, "Chicken (Kienyeji)": 900
}

# Added 'manure_rate' (kg/day) and 'biogas_yield' (m3/kg) for Green Cycle
SPECIES_INFO = {
    "Beef": {"target": 450.0, "ch4": 0.18, "manure": 12.0, "biogas": 0.04}, 
    "Pig": {"target": 130.0, "ch4": 0.04, "manure": 4.0, "biogas": 0.06},
    "Broiler": {"target": 2.5, "ch4": 0.002, "manure": 0.1, "biogas": 0.08},
}

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

# --- 5. HELPER FUNCTIONS ---
def generate_whatsapp_link(df):
    total_profit = df['Profit'].sum()
    total_animals = len(df)
    msg = f"*AEGIS Farm Report* 🇰🇪\n📅 {datetime.now().strftime('%d-%b-%Y')}\n🐂 Animals: {total_animals}\n💰 Profit: KES {total_profit:,.0f}\n🌱 Green Cycle: Active"
    return f"https://wa.me/?text={urllib.parse.quote(msg)}"

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

# --- 6. SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("AEGIS Control")
    choice = st.radio("Navigation", ["Dashboard", "AniWise AI", "Genetics & Breeding", "Help & Docs"])
    st.divider()
    
    with st.expander("📝 Quick Animal Entry", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            animal_id = st.text_input("Tag ID", value=f"UoN-{random.randint(1000,9999)}")
            spec = st.selectbox("Species", list(SPECIES_INFO.keys()))
            col1, col2 = st.columns(2)
            with col1:
                wt_start = st.number_input("Start Wt", value=250.0)
                wt_curr = st.number_input("Current Wt", value=300.0)
            with col2:
                period = st.number_input("Days", value=30)
                feed = st.number_input("Feed (kg)", value=400.0)
            
            sire = st.text_input("Sire ID", value="Unknown")
            dam = st.text_input("Dam ID", value="Unknown")
            
            if st.form_submit_button("Add to Herd"):
                gain = wt_curr - wt_start
                adg = gain / period if period > 0 else 0
                profit = (wt_curr * 760) - (feed * 55)
                methane = period * SPECIES_INFO[spec]["ch4"]
                
                # Green Cycle Calculations
                manure_total = period * SPECIES_INFO[spec]["manure"]
                biogas_potential = manure_total * SPECIES_INFO[spec]["biogas"]
                
                st.session_state.records.append({
                    "ID": animal_id, "Spec": spec, "ADG": adg, "Profit": profit, 
                    "CH4": methane, "FCR": feed/gain if gain > 0 else 0,
                    "Current_Wt": wt_curr, "Sire_ID": sire, "Dam_ID": dam,
                    "Biogas": biogas_potential
                })
                st.rerun()

# --- 7. MAIN INTERFACE ---
if choice == "Dashboard":
    st.title("🐂 AEGIS Smart Farm Dashboard")
    
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        
        # 1. Financials
        m1, m2 = st.columns(2)
        m1.metric("Herd Profit", f"KES {df['Profit'].sum():,.0f}")
        m2.metric("Avg FCR", f"{df['FCR'].mean():.2f}")
        
        st.divider()
        
        # 2. GREEN CYCLE ECONOMY (The "Green" Update)
        st.subheader("♻️ The Green Cycle Economy")
        st.caption("Turning farm waste into energy wealth.")
        
        c_green1, c_green2, c_green3 = st.columns(3)
        
        total_ch4 = df['CH4'].sum()
        total_biogas = df['Biogas'].sum()
        # 1m3 of biogas generates approx 2kWh of electricity or 4 hours of cooking
        cooking_hours = total_biogas * 4 
        
        with c_green1:
            st.metric("Carbon Emissions", f"{total_ch4:.2f} kg", delta="Target: 0")
        
        with c_green2:
            st.metric("Biogas Potential", f"{total_biogas:.2f} m³", delta=f"~{int(cooking_hours)} Cooking Hours", delta_color="normal")
            
        with c_green3:
            # Calculating Fertilizer savings (1 ton manure ~ 2000 KES value)
            manure_value = (total_biogas * 25) # Rough estimate
            st.metric("Fertilizer Savings", f"KES {manure_value:.0f}", delta="From Manure")

        # 3. VISUALS
        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Performance Analytics")
            chart = alt.Chart(df).mark_bar().encode(
                x='ID', y='ADG', color='Spec', tooltip=['ID', 'Profit', 'FCR']
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
        
        with c2:
            st.subheader("Manager Actions")
            whatsapp_url = generate_whatsapp_link(df)
            st.link_button("📲 Share Report (WhatsApp)", whatsapp_url)
            
            if st.button("Clear All Records"):
                st.session_state.records = []
                st.rerun()
                
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Your dashboard is empty. Use the sidebar to add animals.")

elif choice == "AniWise AI":
    st.title("🤖 AniWise: Humanitarian Sentinel")
    
    # Initialize 'results' to avoid NameError flaw
    results = []
    
    with st.expander("🌍 Live Regional Outbreak Alerts", expanded=True):
        news = get_livestock_outbreaks()
        if news:
            for art in news:
                st.warning(f"🔔 **{art['source']['name']}**: {art['title']}")
                st.caption(f"[Read Full Alert]({art['url']})")
        else:
            st.info("No active outbreaks detected in global feeds today.")

    col_in, col_diag = st.columns([1, 1])
    with col_in:
        st.subheader("📋 Clinical Assessment")
        duration = st.slider("Days since onset:", 0, 30, 1)
        all_signs = sorted(list(set([s for d in GLOBAL_VET_DB.values() for s in d["symptoms"].keys()])))
        selected = st.multiselect("Identify observed signs:", all_signs)

    with col_diag:
        st.subheader("🩺 Diagnostic Analysis")
        if selected:
            for dis, data in GLOBAL_VET_DB.items():
                score = sum(data["symptoms"][s] for s in selected if s in data["symptoms"])
                if duration >= data["time_range"][0] and duration <= data["time_range"][1]: score += 2
                if data["key"] not in selected: score *= 0.4
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
        else:
            st.info("Select symptoms to activate AI.")

    # National Reporting - Now Protected against 'Flaws'
    if st.session_state.records and selected and results:
        st.divider()
        st.subheader("📢 National Reporting")
        report_animal = st.selectbox("Confirm Animal:", [r['ID'] for r in st.session_state.records])
        top = sorted(results, key=lambda x: x['conf'], reverse=True)[0]
        if top['conf'] > 65:
            if st.button("🚀 TRANSMIT DATA TO VETERINARY SERVICES"):
                st.balloons()
                st.success(f"Report Transmitted for {report_animal}. Tracking ID: AEGIS-{random.randint(100,999)}")

elif choice == "Genetics & Breeding":
    if st.session_state.records:
        render_genetics_tab(pd.DataFrame(st.session_state.records))
    else: st.warning("No data found.")

elif choice == "Help & Docs":
    st.title("📚 AEGIS Field Guide")
    st.info("Offline Manual for Rural Operations.")
    
    tab1, tab2, tab3 = st.tabs(["Diagnostics", "Weight Estimation", "Green Cycle"])
    
    with tab1:
        st.subheader("Vital Signs Reference")
        st.markdown("""
        - **Temperature:** Normal cattle temp is **38.5°C**.
        - **Lymph Nodes:** Hard swelling under the ear often means **ECF**.
        - **Dehydration:** Skin pinch test > 2 seconds.
        """)
        # Placeholder for images
    
    with tab2:
        st.subheader("Heart Girth Method")
        st.markdown("Formula: `Weight (kg) = (Heart Girth cm)² / 300`")
        
    with tab3:
        st.subheader("The Green Cycle")
        st.markdown("""
        **Don't waste the waste!**
        - Cow dung can be digested to produce **Biogas** for cooking.
        - The remaining slurry is a high-grade **Nitrogen Fertilizer** for crops.
        - AEGIS calculates this value automatically in the Dashboard.
        """)
        

st.divider()
st.caption("Eric Kamau | AEGIS Project | UoN Animal Production Research")
