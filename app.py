import streamlit as st

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="UoN Livestock Analytics", page_icon="🐄")

# --- 2. PROFESSIONAL HEADER ---
st.title("🐄 Livestock Enterprise Analytics")
st.subheader("University of Nairobi | Animal Production Dept")
st.markdown("---")

# --- 3. SIDEBAR INPUTS (Industry Benchmarks) ---
st.sidebar.header("Market Data (KES)")
price_per_kg = st.sidebar.number_input("Market Price (KES/kg)", value=210)
feed_cost = st.sidebar.number_input("Feed Cost (KES/kg)", value=45)

# --- 4. MAIN INTERFACE ---
col1, col2 = st.columns(2)

with col1:
    st.header("Animal Metrics")
    species = st.selectbox("Select Species", ["Beef", "Pig", "Broiler"])
    initial_wt = st.number_input("Initial Weight (kg)", min_value=0.0, value=250.0)
    current_wt = st.number_input("Current Weight (kg)", min_value=0.0, value=300.0)

with col2:
    st.header("Production Data")
    days = st.number_input("Days in Period", min_value=1, value=30)
    feed_used = st.number_input("Total Feed Consumed (kg)", min_value=0.0, value=400.0)

# --- 5. CALCULATIONS ---
weight_gain = current_wt - initial_wt
adg = weight_gain / days
fcr = feed_used / weight_gain if weight_gain > 0 else 0
revenue = current_wt * price_per_kg
costs = feed_used * feed_cost
profit = revenue - costs

# --- 6. PROFESSIONAL DASHBOARD ---
st.markdown("---")
st.header("📊 Results Dashboard")
m1, m2, m3 = st.columns(3)
m1.metric("Avg Daily Gain (ADG)", f"{adg:.2f} kg")
m2.metric("Feed Conv. Ratio (FCR)", f"{fcr:.2f}")
m3.metric("Net Profit", f"KES {profit:,.2f}")

# --- 7. THE "HOD" INSIGHT ---
if adg < 0.8 and species == "Beef":
    st.warning("⚠️ ADG is below industry standards for Beef. Check feed quality.")
else:
    st.success("✅ Animal performance is within optimal range.")
