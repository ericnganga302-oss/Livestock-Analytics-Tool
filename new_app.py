import streamlit as st
import pandas as pd
import altair as alt
import random
import plotly.express as px

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. DATA & BENCHMARKS ---
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

# --- 3. SESSION STATE ---
if 'records' not in st.session_state: 
    st.session_state.records = []

# --- 4. GENETICS MODULE FUNCTION ---
def render_genetics_tab(df):
    st.header("🧬 Genetic Performance & Lineage")
    st.info("Tracking offspring performance to identify superior Kenyan breeding lines.")

    if not df.empty and 'Sire_ID' in df.columns:
        # 1. Performance by Sire (The "Superior Male" Logic)
        st.subheader("Offspring Performance by Sire")
        # We use current weight as a proxy for genetic potential
        sire_stats = df.groupby('Sire_ID')['Current_Wt'].mean().reset_index()
        sire_stats.columns = ['Sire ID', 'Avg Offspring Weight (kg)']
        
        fig = px.bar(sire_stats, x='Sire ID', y='Avg Offspring Weight (kg)', 
                     color='Avg Offspring Weight (kg)', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

        # 2. Individual Lineage Lookup
        st.divider()
        st.subheader("Quick Pedigree Search")
        animal_list = df['ID'].unique()
        selected_animal = st.selectbox("Select Animal to Trace Lineage", animal_list)
        
        animal_data = df[df['ID'] == selected_animal].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Animal ID", selected_animal)
        c2.metric("Sire (Father)", animal_data.get('Sire_ID', "None"))
        c3.metric("Dam (Mother)", animal_data.get('Dam_ID', "None"))
    else:
        st.warning("No breeding data available yet. Add animals with Sire/Dam info in the sidebar.")

# --- 5. SIDEBAR: DATA ENTRY & NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=80)
    st.title("AEGIS Control")
    
    menu = ["Dashboard", "AniWise AI", "Genetics & Breeding"]
    choice = st.radio("Navigation", menu)
    
    st.divider()
    with st.expander("🇰🇪 Market Intelligence"):
        for meat, price in MARKET_DATA.items():
            st.caption(f"{meat}: KES {price}")

    st.header("📝 New Entry")
    with st.form("entry_form", clear_on_submit=True):
        animal_id = st.text_input("Tag ID", value=f"UoN-{random.randint(1000,9999)}")
        spec = st.selectbox("Species", list(SPECIES_INFO.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            wt_start = st.number_input("Start Wt (kg)", value=250.0)
            wt_curr = st.number_input("Current Wt (kg)", value=300.0)
            sire = st.text_input("Sire (Father) ID", value="Unknown")
        with col2:
            period = st.number_input("Days", value=30)
            feed = st.number_input("Feed (kg)", value=400.0)
            dam = st.text_input("Dam (Mother) ID", value="Unknown")
            
        m_price = st.number_input("Market Price (KES/kg)", value=760.0)
        f_price = st.number_input("Feed Price (KES/kg)", value=55.0)
        
        if st.form_submit_button("Add to Herd"):
            gain = wt_curr - wt_start
            adg = gain / period if period > 0 else 0
            profit = (wt_curr * m_price) - (feed * f_price)
            methane = period * SPECIES_INFO[spec]["ch4"]
            
            st.session_state.records.append({
                "ID": animal_id, "Spec": spec, "ADG": adg, 
                "Profit": profit, "CH4": methane, 
                "FCR": feed/gain if gain > 0 else 0,
                "Current_Wt": wt_curr, "Sire_ID": sire, "Dam_ID": dam
            })
            st.rerun()

# --- 6. MAIN INTERFACE LOGIC ---
if choice == "Dashboard":
    st.title("🐂 AEGIS Smart Farm Dashboard")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Herd Profit", f"KES {df['Profit'].sum():,.0f}")
        m2.metric("Avg FCR", f"{df['FCR'].mean():.2f}")
        m3.metric("Total CH₄", f"{df['CH4'].sum():.2f} kg")

        # Visuals
        chart = alt.Chart(df).mark_bar().encode(
            x='ID', y='ADG', color='Spec', tooltip=['ID', 'Profit', 'FCR']
        ).properties(height=350)
        st.altair_chart(chart, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
        if st.button("Clear Records"):
            st.session_state.records = []
            st.rerun()
    else:
        st.info("Add animal data in the sidebar to view analytics.")

elif choice == "AniWise AI":
    st.title("🤖 AniWise AI Consultant")
    query = st.text_input("Ask AniWise (e.g. 'Low ADG causes' or 'Methane reduction')")
    if query:
        with st.spinner("Analyzing herd data..."):
            if "adg" in query.lower() or "growth" in query.lower():
                st.success("**AniWise:** Low ADG in Kenyan systems is often linked to protein deficiency. Supplement with cotton seed cake or sunflower meal.")
            elif "methane" in query.lower():
                st.success("**AniWise:** To lower CH4, use Super Napier and ensure proper silage fermentation.")
            else:
                st.write("**AniWise:** Monitoring active. Your FCR is looking stable.")

elif choice == "Genetics & Breeding":
    if st.session_state.records:
        render_genetics_tab(pd.DataFrame(st.session_state.records))
    else:
        st.warning("No data found. Please add livestock entries in the Dashboard first.")

# --- 7. FOOTER ---
st.divider()
st.caption("Eric Kamau | AEGIS Project | UoN Animal Production Research")
