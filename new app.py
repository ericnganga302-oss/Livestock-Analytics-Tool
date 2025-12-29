"""
app.py
Streamlit app for Livestock Enterprise Analytics (upgraded).
Features:
- summary inputs + CSV upload of time series weights
- ADG via linear regression on time-series (more accurate than simple average)
- validation and clear warnings for bad inputs
- charts with Altair, CSV export, and optional SQLite save
"""
import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import io
from datetime import datetime
from math import inf
from metrics import compute_metrics, compute_adg_from_timeseries, estimate_days_to_target

DB_PATH = "livestock_runs.db"

# --- 1. APP CONFIG ---
st.set_page_config(page_title="UoN Livestock Analytics", page_icon="🐄", layout="wide")

st.title("🐄 Livestock Enterprise Analytics (Upgraded)")
st.subheader("University of Nairobi | Animal Production Dept")
st.markdown("---")

# --- 2. SIDEBAR: Market & Settings ---
st.sidebar.header("Market & Feed Settings")
price_per_kg = st.sidebar.number_input("Market Price (KES/kg)", min_value=0.0, value=210.0, step=1.0)
feed_cost = st.sidebar.number_input("Feed Cost (KES/kg feed)", min_value=0.0, value=45.0, step=0.5)

SPECIES_INFO = {
    "Beef": {"target_weight": 450.0, "adg_threshold": 0.8},
    "Pig": {"target_weight": 130.0, "adg_threshold": 0.6},
    "Broiler": {"target_weight": 2.5, "adg_threshold": 0.05},
}

# --- 3. MAIN INPUTS ---
col1, col2 = st.columns(2)
with col1:
    st.header("Animal / Batch Info")
    species = st.selectbox("Species", list(SPECIES_INFO.keys()))
    animal_id = st.text_input("Animal or Batch ID", value="Batch-001")
    initial_wt = st.number_input("Initial Weight (kg)", min_value=0.0, value=250.0, step=0.1)
    target_default = SPECIES_INFO[species]["target_weight"]
    target_wt = st.number_input("Target/Market Weight (kg)", min_value=0.0, value=target_default, step=0.1)

with col2:
    st.header("Period & Feed")
    days = st.number_input("Days in period (summary)", min_value=1, value=30, step=1)
    feed_used = st.number_input("Total Feed Consumed (kg) in period", min_value=0.0, value=400.0, step=0.1)

st.markdown("### Time-series (optional — preferred)")
st.write("Upload CSV with columns: date (YYYY-MM-DD or similar) and weight (kg), or two columns where first is day index and second weight.")
uploaded = st.file_uploader("Upload time-series CSV", type=["csv"])

timeseries_adg = None
ts_df = None
if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        # heuristic: find first numeric column as weight, first column as date/day
        if df.shape[1] < 2:
            st.error("CSV must have at least two columns (date/day, weight).")
        else:
            date_col = df.columns[0]
            weight_col = df.columns[1]
            ts_dates = df[date_col].tolist()
            ts_weights = df[weight_col].tolist()
            timeseries_adg, ts_df = compute_adg_from_timeseries(ts_dates, ts_weights)
            if timeseries_adg is None:
                st.warning("Could not compute ADG from uploaded series (insufficient valid points).")
            else:
                st.success(f"Computed ADG from timeseries: {timeseries_adg:.4f} kg/day")
                # set current weight to last measurement by default
                last_weight = float(ts_df["weight"].iloc[-1])
                current_wt = st.number_input("Current Weight (kg) (from series)", value=last_weight, step=0.1)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        uploaded = None

if uploaded is None:
    current_wt = st.number_input("Current Weight (kg)", min_value=0.0, value=300.0, step=0.1)

# allow user to choose method for ADG
st.markdown("---")
st.header("Compute & Results")
adg_method = st.radio("ADG method", options=["Summary average (weight difference / days)", "Time-series regression (if provided)"], index=1 if timeseries_adg else 0)

# compute adg based on chosen method
if adg_method == "Time-series regression (if provided)":
    adg = timeseries_adg
    if adg is None:
        st.info("No valid time-series ADG; falling back to summary average.")
        adg = None
else:
    adg = None

# If adg still None, compute summary average
if adg is None:
    metrics = compute_metrics(initial_wt, current_wt, days, feed_used, price_per_kg, feed_cost)
    adg = metrics["adg"]
else:
    # compute other metrics using adg and weight gain
    weight_gain = current_wt - initial_wt
    # if timeseries used, fill metrics as well
    metrics = compute_metrics(initial_wt, current_wt, days, feed_used, price_per_kg, feed_cost)
    metrics["adg"] = adg
    # recompute days_to_target using timeseries adg below

# validate
errors = []
if current_wt < 0 or initial_wt < 0 or feed_used < 0:
    errors.append("Negative values detected. Please enter non-negative numbers.")
if days <= 0:
    errors.append("Days must be >= 1.")

if errors:
    for e in errors:
        st.error(e)
    st.stop()

# days-to-target
days_to_target = estimate_days_to_target(current_wt, target_wt, metrics["adg"])

# KPIs display
k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg Daily Gain (ADG)", f"{metrics['adg']:.4f} kg" if metrics["adg"] is not None else "—")
k2.metric("Feed Conversion Ratio (FCR)", f"{metrics['fcr']:.2f}" if metrics["fcr"] is not None else "—")
k3.metric("Cost per kg gain", f"KES {metrics['cost_per_kg_gain']:.2f}" if metrics["cost_per_kg_gain"] is not None else "—")
k4.metric("Net Profit (current)", f"KES {metrics['profit_now']:,.2f}")

st.write(f"Revenue (current): KES {metrics['revenue_now']:,.2f} — Feed costs: KES {metrics['costs']:,.2f}")

# insights
adg_threshold = SPECIES_INFO[species]["adg_threshold"]
if metrics["adg"] is None:
    st.info("Insufficient data to compute ADG.")
else:
    if metrics["adg"] < adg_threshold:
        st.warning(f"⚠️ ADG ({metrics['adg']:.3f} kg/day) is below the benchmark for {species} ({adg_threshold} kg/day).")
    else:
        st.success(f"✅ ADG ({metrics['adg']:.3f} kg/day) is at/above the benchmark for {species}.")

if metrics["fcr"] is None:
    st.info("FCR not available when weight gain is zero or negative.")
elif metrics["fcr"] > 10:
    st.warning("High FCR — verify inputs and animal health.")

# projection chart
st.markdown("### Projection to Target")
if days_to_target == inf:
    st.error("Cannot estimate days to target: ADG is zero or negative.")
else:
    st.write(f"Estimated days to reach {target_wt} kg: {int(days_to_target)} days")
    projection_days = max(int(days_to_target), 30)
    # build projection df
    if ts_df is not None and not ts_df.empty:
        start_day = float(ts_df["day"].iloc[-1])
        start_weight = float(ts_df["weight"].iloc[-1])
        base_day = 0
    else:
        start_day = 0.0
        start_weight = current_wt
        base_day = 0
    adg_for_proj = metrics["adg"] if metrics["adg"] and metrics["adg"] > 0 else 0.0
    df_proj = pd.DataFrame({"day": list(range(0, projection_days + 1))})
    df_proj["weight"] = df_proj["day"] * adg_for_proj + start_weight
    chart = alt.Chart(df_proj).mark_line(point=True).encode(x=alt.X("day", title="Days from now"), y=alt.Y("weight", title="Weight (kg)")).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

# show timeseries if present
if ts_df is not None and not ts_df.empty:
    st.markdown("### Uploaded Time-series")
    st.dataframe(ts_df)
    chart2 = alt.Chart(ts_df).mark_line(point=True).encode(x="day", y="weight")
    st.altair_chart(chart2, use_container_width=True)

# export current run
st.markdown("---")
st.header("Export & Save")
run_data = {
    "timestamp": datetime.utcnow().isoformat(),
    "animal_id": animal_id,
    "species": species,
    "initial_wt": initial_wt,
    "current_wt": current_wt,
    "target_wt": target_wt,
    "days_summary": int(days),
    "feed_used": feed_used,
    "price_per_kg": price_per_kg,
    "feed_cost": feed_cost,
    "weight_gain": metrics["weight_gain"],
    "adg": metrics["adg"],
    "fcr": metrics["fcr"],
    "cost_per_kg_gain": metrics["cost_per_kg_gain"],
    "profit_now": metrics["profit_now"],
}
run_df = pd.DataFrame([run_data])
st.dataframe(run_df.T, height=240)

csv = run_df.to_csv(index=False).encode("utf-8")
st.download_button("Download run data (CSV)", data=csv, file_name=f"{animal_id}_run.csv", mime="text/csv")

# optional save to sqlite
def init_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        animal_id TEXT,
        species TEXT,
        initial_wt REAL,
        current_wt REAL,
        target_wt REAL,
        days_summary INTEGER,
        feed_used REAL,
        price_per_kg REAL,
        feed_cost REAL,
        weight_gain REAL,
        adg REAL,
        fcr REAL,
        cost_per_kg_gain REAL,
        profit_now REAL
    )
    """)
    conn.commit()
    conn.close()

def save_run_to_db(data: dict, path=DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO runs (timestamp, animal_id, species, initial_wt, current_wt, target_wt, days_summary,
                      feed_used, price_per_kg, feed_cost, weight_gain, adg, fcr, cost_per_kg_gain, profit_now)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["timestamp"], data["animal_id"], data["species"], data["initial_wt"], data["current_wt"], data["target_wt"],
        data["days_summary"], data["feed_used"], data["price_per_kg"], data["feed_cost"], data["weight_gain"],
        data["adg"], data["fcr"], data["cost_per_kg_gain"], data["profit_now"]
    ))
    conn.commit()
    conn.close()

if st.button("Initialize local DB (create if missing)"):
    init_db()
    st.success("Initialized local SQLite DB at ./livestock_runs.db")

if st.button("Save this run to local DB"):
    init_db()
    try:
        save_run_to_db(run_data)
        st.success("Saved run.")
    except Exception as e:
        st.error(f"Failed to save run: {e}")

# view saved runs
if st.checkbox("Show saved runs (from local DB)"):
    try:
        conn = sqlite3.connect(DB_PATH)
        df_runs = pd.read_sql_query("SELECT * FROM runs ORDER BY id DESC LIMIT 200", conn)
        st.dataframe(df_runs)
    except Exception as e:
        st.error(f"Could not read DB: {e}")
