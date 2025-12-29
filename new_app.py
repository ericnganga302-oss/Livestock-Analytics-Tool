import streamlit as st
import pandas as pd
import altair as alt
import random

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. MARKET INTELLIGENCE DATA (Kenya Dec 2025) ---
# Prices sourced from Kenya Meat Processors (KMP) & KNBS market trends
MARKET_DATA = {
    "Beef (Bone-in)": 760,
    "Beef (Prime Steak)": 900,
    "Mutton/Goat": 920,
    "Pork (Retail)": 850,
    "Chicken (Whole Capon)": 600,
    "Chicken (Kienyeji)": 900
}

# Average Feed Prices (Retail estimates in KES)
FEED_DATA = {
    "Dairy Meal": 55,
    "Broiler Starter": 72,
    "Layers Mash": 65,
    "Pig Finisher": 52
}

# --- 3. SPECIES BENCHMARKS ---
SPECIES_INFO = {
    "Beef": {"target": 450.0, "adg_min": 0.8, "ch4": 0.18, "icon": "🐂"},
    "Pig": {"target": 130.0, "adg_min": 0.6, "ch4": 0.04, "icon": "🐖"},
    "Broiler": {"target": 2.5, "adg_min": 0.05, "ch4": 0.002, "icon": "🐥"},
}

# --- 4. SESSION STATE ---
if 'records' not in st.session_state: st.session_state.records = []

# --- 5. SIDEBAR: DATA ENTRY & MARKET FEED ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=100)
    st.title("Settings")
    
    with st.expander("🇰🇪 Live Market Intelligence", expanded=True):
        st.write("**Current Wholesale Prices (KES/kg)**")
        for meat, price in MARKET_DATA.items():
            st.caption(f"{meat}: KES {price}")
        st.info("Source: KMP/KNBS Dec 2025 Trends")

    st.header("🧬 New Entry")
    with st.form("entry_form", clear_on_submit=True):
        animal_id = st.text_input("Tag ID", value=f"UoN-{random.randint(1000,9999)}")
        spec = st.selectbox("Species", list(SPECIES_INFO.keys()))
        col1, col2 = st.columns(2)
        with col1:
            wt_start = st.number_input("Start Wt (kg)", value=250.0)
            wt_curr = st.number_input("Current Wt (kg)", value=300.0)
        with col2:
            period = st.number_input("Days", value=30)
            feed = st.number_input("Feed (kg)", value=400.0)
        
        m_price = st.number_input("Market Price (KES/kg)", value=760.0)
        f_price = st.number_input("Feed Price (KES/kg)", value=55.0)
        
        if st.form_submit_button("Add Animal"):
            gain = wt_curr - wt_start
            adg = gain / period
            profit = (wt_curr * m_price) - (feed * f_price)
            methane = period * SPECIES_INFO[spec]["ch4"]
            st.session_state.records.append({
                "ID": animal_id, "Spec": spec, "ADG": adg, 
                "Profit": profit, "CH4": methane, "FCR": feed/gain if gain > 0 else 0
            })
            st.rerun()

# --- 6. ANIWISE AI CONSULTANT ---
st.title("🐂 AEGIS Smart Farm Dashboard")
st.divider()

col_ani, col_main = st.columns([1, 2])

with col_ani:
    st.subheader("🤖 AniWise AI Consultant")
    st.write("Expert Troubleshooting & Insights")
    
    query = st.text_input("Ask AniWise (e.g. 'Low ADG causes' or 'Methane reduction')")
    
    if query:
        with st.spinner("AniWise is analyzing..."):
            if "adg" in query.lower() or "growth" in query.lower():
                st.write("**AniWise Recommendation:** Low Average Daily Gain (ADG) in Kenyan systems is often linked to **Protein Deficiency** or **Internal Parasites**. Consider deworming every 3 months and supplementing with 18% Crude Protein (CP) concentrates.")
            elif "methane" in query.lower() or "environment" in query.lower():
                st.write("**AniWise Recommendation:** To reduce methane intensity, improve forage quality. Feeding highly digestible grasses like **Super Napier (Pakchong 1)** reduces fermentation time in the rumen, lowering gas emissions per kg of meat.")
            else:
                st.write("**AniWise:** I am monitoring your herd data. Currently, I recommend optimizing the Feed Conversion Ratio (FCR) for your latest entries.")

# --- 7. ANALYTICS ---
with col_main:
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
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
        if st.button("Clear Records"):
            st.session_state.records = []
            st.rerun()
    else:
        st.info("Welcome to AEGIS Pro. Please enter animal data in the sidebar to activate the AI Consultant and Market Analytics.")

# --- 8. FOOTER ---
st.caption("Developed for UoN Animal Production Research | Powered by AniWise AI Logic")
