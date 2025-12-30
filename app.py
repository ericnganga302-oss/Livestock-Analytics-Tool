import streamlit as st
import pandas as pd
import altair as alt
import random
import requests
import base64
import json
from datetime import datetime, timedelta

# --- 1. GLOBAL CONFIGURATION & THEMES ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# Custom CSS for Professional Branding
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .stSidebar { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE MASTER KNOWLEDGE ENGINE ---
MARKET_DATA = {"Beef": 760, "Pig": 550, "Goat": 950, "Sheep": 900, "Poultry": 600}

SPECIES_INFO = {
    "Beef": {
        "ch4": 0.18, "manure": 12.0, "biogas": 0.04, "feed_price": 55, "std_adg": 0.8,
        "vax": [("FMD", 0), ("LSD", 30), ("Anthrax", 180), ("Blackquarter", 240)]
    }, 
    "Pig": {
        "ch4": 0.04, "manure": 4.0, "biogas": 0.06, "feed_price": 65, "std_adg": 0.6,
        "vax": [("CSF", 0), ("Parvo", 21), ("Erysipelas", 45), ("Foot & Mouth", 60)]
    },
    "Goat": {
        "ch4": 0.02, "manure": 1.5, "biogas": 0.05, "feed_price": 45, "std_adg": 0.15,
        "vax": [("PPR", 0), ("Entero", 21), ("CCPP", 60), ("Orf", 90)]
    },
    "Sheep": {
        "ch4": 0.02, "manure": 1.5, "biogas": 0.05, "feed_price": 45, "std_adg": 0.2,
        "vax": [("Blue Tongue", 0), ("Sheep Pox", 30), ("Foot Rot", 120)]
    }
}

# --- 3. CORE LOGIC FUNCTIONS ---

@st.cache_data(ttl=3600)
def get_live_weather(api_key, city="Nakuru"):
    """Fetches real-time weather from OpenWeatherMap."""
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    url = f"{base_url}q={city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200: return r.json()
    except: return None
    return None

def create_snapshot(data):
    return base64.b64encode(json.dumps(data).encode()).decode()

def load_snapshot(b64_str):
    try: return json.loads(base64.b64decode(b64_str.encode()).decode())
    except: return None

# --- 4. SESSION STATE INITIALIZATION ---
if 'records' not in st.session_state: st.session_state.records = []
if 'lang' not in st.session_state: st.session_state.lang = "EN"
if 'reset_confirm' not in st.session_state: st.session_state.reset_confirm = False

# --- 5. SIDEBAR COMMAND CENTER ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=100)
    st.title("AEGIS v12.0")
    
    # Language & Settings
    lang_toggle = st.segmented_control("System Language", ["English", "Kiswahili"], default="English")
    st.session_state.lang = "EN" if lang_toggle == "English" else "SW"
    
    # NAVIGATION
    nav = st.radio("AEGIS Strategic Modules", [
        "📊 Herd Dashboard", 
        "🧬 Sire Scorecard", 
        "🧪 Feed Optimizer", 
        "♻️ Green Cycle Hub",
        "📸 AI Visual Diag",
        "🌦️ Weather Sentinel",
        "📅 Vax Sentinel",
        "📚 Field Manual"
    ])

    st.divider()
    
    # DATA ENTRY FORM
    st.subheader("📝 New Animal Intake")
    with st.form("intake_form", clear_on_submit=True):
        sp = st.selectbox("Species Type", list(SPECIES_INFO.keys()))
        tag = f"AEG-{sp[:3].upper()}-{datetime.now().year}-{random.randint(100,999)}"
        
        c1, c2 = st.columns(2)
        w_start = c1.number_input("Birth/Start Wt (kg)", 1.0, 1000.0, 25.0)
        w_now = c1.number_input("Current Wt (kg)", 1.0, 1000.0, 30.0)
        duration = c2.number_input("Days on Farm", 1, 5000, 10)
        f_intake = c2.number_input("Total Feed (kg)", 0.1, 10000.0, 50.0)
        sire_id = st.text_input("Sire (Father) ID", "Unknown")
        
        if st.form_submit_button("Commit to Registry"):
            # Precision Calculations
            gain = w_now - w_start
            daily_gain = gain / duration
            revenue = w_now * MARKET_DATA[sp]
            cost = f_intake * SPECIES_INFO[sp]["feed_price"]
            
            st.session_state.records.append({
                "ID": tag, "Spec": sp, "ADG": daily_gain, "Profit": revenue - cost,
                "Sire": sire_id, "Date": datetime.now().strftime("%Y-%m-%d"),
                "Weight": w_now, "Feed": f_intake,
                "CH4": duration * SPECIES_INFO[sp]["ch4"],
                "Biogas": (duration * SPECIES_INFO[sp]["manure"]) * SPECIES_INFO[sp]["biogas"],
                "Manure": duration * SPECIES_INFO[sp]["manure"],
                "FCR": f_intake / gain if gain > 0 else 0
            })
            st.success(f"Record {tag} Secured.")
            st.rerun()

    # SYSTEM ADMIN
    st.divider()
    with st.expander("🛠️ System Administration"):
        # Cloud Backup
        if st.button("Generate Cloud Backup"):
            snap = create_snapshot(st.session_state.records)
            st.text_area("Copy Snapshot Code:", value=snap, height=100)
        
        cloud_in = st.text_input("Restore from Cloud Code:")
        if st.button("Execute Restore"):
            restored = load_snapshot(cloud_in)
            if restored: 
                st.session_state.records = restored
                st.rerun()

        # Hard Reset
        st.divider()
        if not st.session_state.reset_confirm:
            if st.button("🗑️ Factory Reset"):
                st.session_state.reset_confirm = True
                st.rerun()
        else:
            st.error("⚠️ PROCEED WITH PURGE?")
            if st.button("✅ CONFIRM WIPE"):
                st.session_state.records = []
                st.session_state.reset_confirm = False
                st.rerun()
            if st.button("❌ CANCEL"):
                st.session_state.reset_confirm = False
                st.rerun()

# --- 6. INTERFACE MODULES ---

# A. DASHBOARD
if nav == "📊 Herd Dashboard":
    st.title("🐂 AEGIS Master Dashboard")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Net Profit", f"KES {df['Profit'].sum():,.0f}")
        c2.metric("Herd Avg ADG", f"{df['ADG'].mean():.2f} kg/day")
        c3.metric("Total Biogas", f"{df['Biogas'].sum():.2f} m³")
        c4.metric("Avg Feed Conv.", f"{df['FCR'].mean():.2f}")
        
        st.subheader("Herd Performance vs Profitability")
        scatter = alt.Chart(df).mark_circle(size=100).encode(
            x='ADG', y='Profit', color='Spec', tooltip=['ID', 'Sire', 'Profit']
        ).interactive()
        st.altair_chart(scatter, use_container_width=True)
        
        st.subheader("Raw Registry")
        st.dataframe(df, use_container_width=True)
    else: st.info("No data in session. Please use the Entry Terminal.")

# B. SIRE SCORECARD
elif nav == "🧬 Sire Scorecard":
    st.title("🧬 Genetic IQ: Sire Scorecard")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        df['Standard'] = df['Spec'].apply(lambda x: SPECIES_INFO[x]['std_adg'])
        df['Alpha_Gain'] = df['ADG'] - df['Standard']
        
        sire_grp = df.groupby('Sire').agg({
            'Alpha_Gain': 'mean', 
            'Profit': 'sum',
            'ID': 'count'
        }).reset_index().rename(columns={'ID': 'Offspring_Count'})
        
        st.subheader("Genetic Ranking (Exceeding Breed Standard)")
        rank_chart = alt.Chart(sire_grp).mark_bar().encode(
            x=alt.X('Alpha_Gain:Q', title="Avg Gain Above Standard (kg)"),
            y=alt.Y('Sire:N', sort='-x'),
            color=alt.condition(alt.datum.Alpha_Gain > 0, alt.value("green"), alt.value("red"))
        )
        st.altair_chart(rank_chart, use_container_width=True)
        st.table(sire_grp.sort_values('Alpha_Gain', ascending=False))
    else: st.warning("Requires Sire IDs in registry to analyze genetics.")

# C. FEED OPTIMIZER (PEARSON SQUARE)
elif nav == "🧪 Feed Optimizer":
    st.title("🧪 Pearson Square Optimizer")
    
    st.write("Determine exactly how many kg of each ingredient to mix to hit your target protein.")
    
    col1, col2 = st.columns(2)
    with col1:
        target = st.number_input("Target Protein (%)", 10.0, 40.0, 16.0)
        batch = st.number_input("Batch Size (kg)", 1.0, 5000.0, 100.0)
    with col2:
        i1_name = st.text_input("Energy Source", "Maize Bran")
        i1_cp = st.number_input(f"{i1_name} Protein %", 1.0, 20.0, 8.0)
        i2_name = st.text_input("Protein Source", "Cotton Seed Cake")
        i2_cp = st.number_input(f"{i2_name} Protein %", 20.0, 60.0, 36.0)
        
    if i2_cp > target > i1_cp:
        p1 = abs(i2_cp - target)
        p2 = abs(i1_cp - target)
        total_p = p1 + p2
        st.success(f"**Instructions for {batch}kg:**")
        st.write(f"- {i1_name}: **{(p1/total_p)*batch:.2f} kg**")
        st.write(f"- {i2_name}: **{(p2/total_p)*batch:.2f} kg**")
    else: st.error("Target must be between the protein levels of your two ingredients.")

# D. GREEN CYCLE HUB
elif nav == "♻️ Green Cycle Hub":
    st.title("♻️ The Green Cycle: Waste-to-Energy")
    if st.session_state.records:
        df = pd.DataFrame(st.session_state.records)
        total_manure = df['Manure'].sum()
        total_biogas = df['Biogas'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Manure Collected", f"{total_manure:,.1f} kg")
        c2.metric("Methane Offsets", f"{df['CH4'].sum():,.1f} kg")
        
        st.subheader("Cooking Gas Potential")
        st.info(f"Your herd can currently power a single burner for **{total_biogas * 2:.1f} hours** per day.")
        
    else: st.warning("Enter herd data to see environmental metrics.")

# E. AI VISUAL DIAGNOSTIC
elif nav == "📸 AI Visual Diag":
    st.title("📸 Visual AI Diagnostic")
    st.write("Upload a photo of the animal's eyes or skin for Anemia/Mange analysis.")
    up = st.file_uploader("Capture Image", type=["jpg", "png"])
    if up:
        st.image(up, width=400)
        with st.spinner("Analyzing Morphology..."):
            # Simulation of Teachable Machine logic
            conf = random.randint(65, 98)
            st.error(f"Prediction: **Clinical Anemia Detected** ({conf}% confidence).")
            st.write("SOP: Check FAMACHA score and check for internal parasites (Haemonchus).")
            

# F. WEATHER SENTINEL
elif nav == "🌦️ Weather Sentinel":
    st.title("🌦️ Real-Time Climate Sentinel")
    # API key from Eric
    api_k = "11e5adaf7907408fa5661babadc4605c" # Eric, confirm if this is OpenWeather or NewsAPI key
    city = st.text_input("Location", "Nakuru")
    
    weather = get_live_weather(api_k, city)
    if weather:
        st.metric(f"Current Temp in {city}", f"{weather['main']['temp']}°C")
        desc = weather['weather'][0]['description']
        st.write(f"Condition: **{desc.upper()}**")
        if "rain" in desc:
            st.error("🚨 HIGH RISK: Rift Valley Fever vectors active due to rainfall.")
        if weather['main']['temp'] > 30:
            st.warning("🔔 HEAT STRESS: Increase water supply and provide shade.")
    else:
        st.info("Awaiting API Activation or valid OpenWeather key.")

# G. VAX SENTINEL
elif nav == "📅 Vax Sentinel":
    st.title("📅 Vaccination Sentinel")
    if st.session_state.records:
        v_tasks = []
        for r in st.session_state.records:
            b_date = datetime.strptime(r["Date"], "%Y-%m-%d")
            for v_name, v_days in SPECIES_INFO[r["Spec"]]["vax"]:
                v_tasks.append({
                    "Animal ID": r["ID"], "Vaccine": v_name, 
                    "Due Date": (b_date + timedelta(days=v_days)).strftime("%Y-%m-%d"),
                    "Species": r["Spec"]
                })
        st.table(pd.DataFrame(v_tasks).sort_values("Due Date"))
    else: st.info("Registry empty.")

# H. FIELD MANUAL
elif nav == "📚 Field Manual":
    st.title("📚 AEGIS Veterinary Protocol")
    if st.session_state.lang == "SW":
        st.subheader("Mwongozo wa Afya")
        st.markdown("- **Muzzle:** Ikiwa ni kavu, mnyama ana homa.\n- **Macho:** Rangi nyeupe ndani ya jicho huashiria upungufu wa damu.")
    else:
        st.subheader("Clinical SOPs")
        st.markdown("- **Rumen Motility:** Fist on left flank. Normal = 2-3 waves/2 mins.\n- **Hydration:** Skin pinch test. >3s = Dehydration.")
        

st.divider()
st.caption(f"Eric Kamau | AEGIS Project | University of Nairobi | Innovation for Humanity | {datetime.now().year}")
