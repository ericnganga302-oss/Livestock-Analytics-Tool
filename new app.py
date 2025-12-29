import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from math import inf

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="AEGIS Livestock Analytics",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. MINIMAL STYLE INJECTION (use with care) ---
st.markdown(
    """
    <style>
    /* lightweight styling that is less dependent on Streamlit internal class names */
    .app-title { font-size:22px; font-weight:600; }
    .kpi-card { background: #fff; padding: 10px 12px; border-radius:8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. CONSTANTS, BENCHMARKS & ECO-FACTORS ---
SPECIES_INFO = {
    "Beef": {"target_weight": 450.0, "adg_threshold": 0.8, "icon": "🐂", "ch4": 0.18},
    "Pig": {"target_weight": 130.0, "adg_threshold": 0.6, "icon": "🐖", "ch4": 0.04},
    "Broiler": {"target_weight": 2.5, "adg_threshold": 0.05, "icon": "🐥", "ch4": 0.002},
}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    price_per_kg = st.number_input("Market Price (KES/kg)", min_value=0.0, value=210.0, step=1.0, help="Price per kg liveweight")
    feed_cost = st.number_input("Feed Cost (KES/kg feed)", min_value=0.0, value=45.0, step=0.5, help="Cost per kg of feed")
    st.divider()
    st.info("Climate-Smart Edition: Tracking growth and methane efficiency.")

# --- 5. MAIN INTERFACE ---
st.markdown('<div class="app-title">🐄 Livestock Enterprise Analytics</div>', unsafe_allow_html=True)
st.caption("University of Nairobi | Animal Production Department | Decision Support System")

col1, col2, col3 = st.columns(3)
with col1:
    species = st.selectbox("Species Type", list(SPECIES_INFO.keys()))
    initial_wt = st.number_input("Starting Weight (kg)", min_value=0.0, value=250.0, step=0.1)
with col2:
    current_wt = st.number_input("Current Weight (kg)", min_value=0.0, value=300.0, step=0.1)
    days = st.number_input("Days in Period", min_value=1, value=30, step=1)
with col3:
    target_wt = st.number_input("Target Weight (kg)", min_value=0.0, value=float(SPECIES_INFO[species]["target_weight"]), step=0.1)
    feed_used = st.number_input("Total Feed Used (kg)", min_value=0.0, value=400.0, step=0.1)

st.markdown("### Optional: Upload time-series weights (date,weight) to compute ADG from real measurements")
upload = st.file_uploader("Upload CSV (date or day, weight)", type=["csv"])

# --- 6. HELPERS ---
def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return None

def compute_adg_from_timeseries(df):
    """
    Expect df with two columns: date/day and weight.
    If first column parses to datetime, compute day offsets; else treat as numeric days.
    Returns adg (kg/day) and prepared dataframe (day, weight).
    """
    if df.shape[1] < 2:
        return None, None
    dcol = df.columns[0]
    wcol = df.columns[1]
    try:
        df = df[[dcol, wcol]].dropna()
        # try parse dates
        dates = pd.to_datetime(df[dcol], errors="coerce")
        if dates.notna().sum() >= 2:
            df["day"] = (dates - dates.iloc[0]).dt.total_seconds() / (24*3600)
        else:
            df["day"] = pd.to_numeric(df[dcol], errors="coerce") - pd.to_numeric(df[dcol], errors="coerce").iloc[0]
        df["weight"] = pd.to_numeric(df[wcol], errors="coerce")
        df = df.dropna(subset=["day", "weight"])
        if len(df) < 2:
            return None, None
        x = df["day"].to_numpy()
        y = df["weight"].to_numpy()
        m, c = np.polyfit(x, y, 1)
        return float(m), df[["day", "weight"]].reset_index(drop=True)
    except Exception:
        return None, None

def estimate_days_to_target(current_wt, target_wt, adg):
    if target_wt <= current_wt:
        return 0.0
    if adg is None or adg <= 0:
        return inf
    remaining = target_wt - current_wt
    return remaining / adg

# --- 7. ADG FROM TIMESERIES (OPTIONAL) ---
timeseries_adg = None
ts_df = None
if upload:
    try:
        df_in = pd.read_csv(upload)
        timeseries_adg, ts_df = compute_adg_from_timeseries(df_in)
        if timeseries_adg is not None:
            st.success(f"Computed ADG from uploaded series: {timeseries_adg:.4f} kg/day")
            # optionally overwrite current weight to last measured point
            last_w = float(ts_df["weight"].iloc[-1])
            current_wt = st.number_input("Current Weight (kg) (from series)", value=last_w, step=0.1)
        else:
            st.warning("Could not compute ADG from uploaded file — ensure file has two columns (date/day, weight) and ≥2 valid rows.")
    except Exception as e:
        st.error(f"Failed to read uploaded CSV: {e}")

# --- 8. CALCULATIONS & VALIDATION ---
if current_wt < initial_wt:
    st.error("🚨 Input Error: Current weight must be equal or greater than Initial weight.")
    st.stop()

weight_gain = current_wt - initial_wt
# ADG: prefer timeseries ADG if available
adg = timeseries_adg if timeseries_adg is not None else safe_div(weight_gain, days)
fcr = safe_div(feed_used, weight_gain) if weight_gain > 0 else None

# profit: show both current gross value and incremental profit for the period
revenue_now = current_wt * price_per_kg
revenue_gain = weight_gain * price_per_kg
feed_costs = feed_used * feed_cost
profit_incremental = revenue_gain - feed_costs
profit_current_value = revenue_now - feed_costs

daily_methane = SPECIES_INFO[species]["ch4"]
total_methane_period = days * daily_methane
days_to_target = estimate_days_to_target(current_wt, target_wt, adg)

# methane intensity (kg CH4 per kg gain) — guard for zero gain
methane_intensity = safe_div(total_methane_period, weight_gain) if weight_gain > 0 else None

# --- 9. DASHBOARD ---
st.divider()
adg_target = SPECIES_INFO[species]["adg_threshold"]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg Daily Gain (ADG)", f"{adg:.3f} kg" if adg is not None else "—", delta=f"{adg - adg_target:.3f} vs target" if adg is not None else "")
k2.metric("Feed Conversion Ratio (FCR)", f"{fcr:.2f}" if fcr is not None else "—", delta="Lower is better")
k3.metric("Methane (CH₄) — period", f"{total_methane_period:.3f} kg", delta=f"{daily_methane:.3f} kg/day")
k4.metric("Profit (period)", f"KES {profit_incremental:,.0f}", help="Revenue from weight gain minus feed cost for this period")

st.write(f"Gross value (current weight): KES {revenue_now:,.2f} — Feed cost (period): KES {feed_costs:,.2f} — Net (current): KES {profit_current_value:,.2f}")

# insights
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("🩺 Expert Recommendations")
    if adg is None:
        st.info("Insufficient data to compute ADG. Upload time-series or provide valid summary inputs.")
    else:
        if adg < adg_target:
            st.warning("⚠️ Growth below benchmark. Check nutrition, parasite control, and health management.")
        else:
            st.success("✅ Growth on track. Management appears efficient.")

    st.subheader("💰 Cost-Benefit Simulator")
    expected_boost = st.slider("Boost ADG by (kg/day) using better feed", 0.0, 0.5, 0.1, step=0.01)
    if adg is not None and adg > 0:
        new_adg = adg + expected_boost
        if days_to_target != inf:
            new_days_to_target = estimate_days_to_target(current_wt, target_wt, new_adg)
            days_saved = None
            if new_days_to_target != inf:
                days_saved = max(0, int(days_to_target - new_days_to_target)) if days_to_target != inf else None
            if days_saved is not None:
                st.write(f"Estimated days saved to reach target: **{days_saved} days**")
        else:
            st.info("Cannot estimate days to target with current ADG (zero/negative).")

with c2:
    st.subheader("🌱 Sustainability Impact")
    if days_to_target == inf:
        st.info("Cannot compute lifecycle methane projection: ADG is zero or negative.")
    else:
        total_life_methane = (days + max(0.0, days_to_target)) * daily_methane
        st.write(f"Total methane (period + remaining to target): **{total_life_methane:.2f} kg CH₄**")
        if methane_intensity is not None:
            st.write(f"Methane intensity (kg CH₄ per kg weight gain in period): **{methane_intensity:.3f}**")
        eco_df = pd.DataFrame({
            "Category": ["Emitted (period)", "Remaining to Target"],
            "Methane (kg)": [total_methane_period, (days_to_target * daily_methane) if days_to_target != inf else 0.0]
        })
        eco_chart = alt.Chart(eco_df).mark_bar().encode(
            x=alt.X("Category:N"),
            y=alt.Y("Methane (kg):Q"),
            color="Category:N"
        ).properties(height=220)
        st.altair_chart(eco_chart, use_container_width=True)

# --- 10. OPTIONAL: timeseries preview & projection chart ---
if ts_df is not None:
    st.markdown("### Uploaded time-series")
    st.dataframe(ts_df)
    chart_ts = alt.Chart(ts_df).mark_line(point=True).encode(x="day", y="weight").properties(height=240)
    st.altair_chart(chart_ts, use_container_width=True)

# projection
st.markdown("### Projection to Target (linear projection based on ADG)")
if adg is None or adg <= 0:
    st.info("Projection unavailable: ADG must be positive.")
else:
    if days_to_target == inf:
        st.info("ADG > 0 is required for projection.")
    else:
        proj_days = max(30, int(days_to_target))
        proj_df = pd.DataFrame({"day": list(range(0, proj_days + 1))})
        proj_df["weight"] = current_wt + proj_df["day"] * adg
        chart_proj = alt.Chart(proj_df).mark_line(point=True).encode(x=alt.X("day", title="Days from now"), y=alt.Y("weight", title="Weight (kg)"))
        st.altair_chart(chart_proj, use_container_width=True)

# --- 11. FOOTER & EXPORT ---
st.sidebar.markdown("---")
st.sidebar.caption("Eco-Score: Efficiency = Sustainability")

# small export
summary = {
    "species": species,
    "initial_wt": initial_wt,
    "current_wt": current_wt,
    "weight_gain": weight_gain,
    "adg": adg,
    "fcr": fcr,
    "profit_incremental": profit_incremental,
    "total_methane_period": total_methane_period,
    "methane_intensity": methane_intensity,
}
st.download_button("Download run summary (CSV)", data=pd.DataFrame([summary]).to_csv(index=False), file_name="run_summary.csv", mime="text/csv")
