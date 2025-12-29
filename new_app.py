import streamlit as st
import pandas as pd
import altair as alt
import random
import sqlite3
from datetime import datetime
from typing import List, Optional

# --------------------
# CONFIG
# --------------------
st.set_page_config(page_title="AEGIS Livestock Pro (Persistent)", page_icon="🧬", layout="wide")
DB_PATH = "livestock_runs.db"

MARKET_DATA = {
    "Beef (Bone-in)": 760,
    "Beef (Prime Steak)": 900,
    "Mutton/Goat": 920,
    "Pork (Retail)": 850,
    "Chicken (Whole Capon)": 600,
    "Chicken (Kienyeji)": 900,
}

FEED_DATA = {
    "Dairy Meal": 55,
    "Broiler Starter": 72,
    "Layers Mash": 65,
    "Pig Finisher": 52
}

SPECIES_INFO = {
    "Beef": {"target_weight": 450.0, "adg_min": 0.8, "ch4": 0.18, "icon": "🐂"},
    "Pig": {"target_weight": 130.0, "adg_min": 0.6, "ch4": 0.04, "icon": "🐖"},
    "Broiler": {"target_weight": 2.5, "adg_min": 0.05, "ch4": 0.002, "icon": "🐥"},
}

# --------------------
# HELPERS (DB + MATH)
# --------------------
def safe_div(a: float, b: float) -> Optional[float]:
    try:
        return a / b
    except Exception:
        return None

def init_db(path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        animal_id TEXT,
        species TEXT,
        start_weight REAL,
        current_weight REAL,
        days INTEGER,
        feed_used REAL,
        market_price REAL,
        feed_price REAL,
        adg REAL,
        profit REAL,
        methane REAL,
        fcr REAL
    )
    """)
    conn.commit()
    conn.close()

def save_record_to_db(record: dict, path: str = DB_PATH):
    init_db(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO runs (timestamp, animal_id, species, start_weight, current_weight, days, feed_used, market_price, feed_price, adg, profit, methane, fcr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("Timestamp", datetime.utcnow().isoformat()),
        record.get("ID"),
        record.get("Species"),
        float(record.get("StartWeight", 0.0)) if record.get("StartWeight") is not None else None,
        float(record.get("CurrentWeight", 0.0)) if record.get("CurrentWeight") is not None else None,
        int(record.get("Days", 0)) if record.get("Days") is not None else None,
        float(record.get("FeedUsed", 0.0)) if record.get("FeedUsed") is not None else None,
        float(record.get("MarketPrice", 0.0)) if record.get("MarketPrice") is not None else None,
        float(record.get("FeedPrice", 0.0)) if record.get("FeedPrice") is not None else None,
        float(record.get("ADG", 0.0)) if record.get("ADG") is not None else None,
        float(record.get("Profit", 0.0)) if record.get("Profit") is not None else None,
        float(record.get("CH4", 0.0)) if record.get("CH4") is not None else None,
        float(record.get("FCR", 0.0)) if record.get("FCR") is not None else None,
    ))
    conn.commit()
    conn.close()

def save_records_to_db(records: List[dict], path: str = DB_PATH):
    for r in records:
        save_record_to_db(r, path=path)

def load_db_records(path: str = DB_PATH, limit: int = 1000) -> pd.DataFrame:
    try:
        init_db(path)
        conn = sqlite3.connect(path)
        df = pd.read_sql_query(f"SELECT * FROM runs ORDER BY id DESC LIMIT {limit}", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def delete_db_records_by_ids(animal_ids: List[str], path: str = DB_PATH):
    if not animal_ids:
        return
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executemany("DELETE FROM runs WHERE animal_id = ?", [(aid,) for aid in animal_ids])
    conn.commit()
    conn.close()

def clear_db(path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("DELETE FROM runs")
    conn.commit()
    conn.close()

# --------------------
# SESSION STATE
# --------------------
if "records" not in st.session_state:
    st.session_state.records = []

# --------------------
# SIDEBAR: ENTRY + DB ACTIONS
# --------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/7/71/University_of_Nairobi_Logo.png/220px-University_of_Nairobi_Logo.png", width=100)
    st.title("AEGIS Settings")

    with st.expander("🇰🇪 Live Market Intelligence", expanded=True):
        st.write("**Wholesale Prices (KES/kg)**")
        for meat, price in MARKET_DATA.items():
            st.caption(f"{meat}: KES {price:,}")
        st.info("Source: KMP/KNBS (Dec 2025) — illustrative")

    st.header("Add Animal (single)")
    with st.form("entry_form", clear_on_submit=True):
        suggested_id = f"UoN-{datetime.utcnow().strftime('%y%m%d')}-{random.randint(1000,9999)}"
        animal_id = st.text_input("Tag ID", value=suggested_id)
        species = st.selectbox("Species", list(SPECIES_INFO.keys()))
        left, right = st.columns(2)
        with left:
            start_wt = st.number_input("Start Weight (kg)", value=250.0, min_value=0.0, step=0.1, format="%.1f")
            curr_wt = st.number_input("Current Weight (kg)", value=300.0, min_value=0.0, step=0.1, format="%.1f")
        with right:
            days = st.number_input("Days (period)", value=30, min_value=1, step=1)
            feed_used = st.number_input("Feed Used (kg)", value=400.0, min_value=0.0, step=0.1)
        default_mprice = MARKET_DATA.get("Beef (Bone-in)", 760)
        mprice = st.number_input("Market Price (KES/kg)", value=float(default_mprice), step=1.0)
        fprice = st.number_input("Feed Price (KES/kg)", value=float(FEED_DATA.get("Dairy Meal", 55)), step=0.1)

        save_immediately = st.checkbox("Save immediately to DB", value=False)
        if st.form_submit_button("Add"):
            gain = curr_wt - start_wt
            if gain <= 0:
                st.error("Current weight must be greater than start weight.")
            else:
                adg = safe_div(gain, days) or 0.0
                profit = (gain * mprice) - (feed_used * fprice)
                methane = days * SPECIES_INFO[species]["ch4"]
                fcr = safe_div(feed_used, gain) or None
                rec = {
                    "ID": animal_id.strip() or suggested_id,
                    "Species": species,
                    "StartWeight": round(start_wt, 2),
                    "CurrentWeight": round(curr_wt, 2),
                    "Days": int(days),
                    "FeedUsed": round(feed_used, 2),
                    "MarketPrice": float(mprice),
                    "FeedPrice": float(fprice),
                    "ADG": round(adg, 4),
                    "Profit": round(profit, 2),
                    "CH4": round(methane, 3),
                    "FCR": round(fcr, 3) if fcr is not None else None,
                    "Timestamp": datetime.utcnow().isoformat()
                }
                st.session_state.records.append(rec)
                st.success(f"Added {rec['ID']} to session.")
                if save_immediately:
                    try:
                        save_record_to_db(rec)
                        st.success("Also saved to local DB.")
                    except Exception as e:
                        st.error(f"Failed saving to DB: {e}")
                st.experimental_rerun()

    st.markdown("---")
    st.header("Session → DB")
    if st.button("Save session records to DB"):
        if st.session_state.records:
            try:
                save_records_to_db(st.session_state.records)
                st.success(f"Saved {len(st.session_state.records)} session record(s) to DB.")
            except Exception as e:
                st.error(f"Failed to save session records: {e}")
        else:
            st.info("No session records to save.")

    if st.button("Clear session records (in-memory)"):
        st.session_state.records = []
        st.success("Cleared session records.")

    st.markdown("---")
    st.header("Database actions")
    if st.button("Clear ALL DB records (DANGER)"):
        clear_db()
        st.success("Cleared database.")

# --------------------
# MAIN APP
# --------------------
st.title("🐂 AEGIS Smart Farm Dashboard — Persistent")
st.caption("Persistent storage via local SQLite + per-species benchmarking visuals")
st.divider()

# Load DB records to show
db_df = load_db_records()

# Session df
session_df = pd.DataFrame(st.session_state.records) if st.session_state.records else pd.DataFrame()

# Combine for benchmarking visuals (avoid column mismatch)
def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = ["ID", "Species", "StartWeight", "CurrentWeight", "Days", "FeedUsed",
            "MarketPrice", "FeedPrice", "ADG", "Profit", "CH4", "FCR", "Timestamp"]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[cols]

session_norm = normalize_df(session_df.copy())
# transform DB df column names to match
if not db_df.empty:
    db_df = db_df.rename(columns={
        "animal_id": "ID", "species": "Species",
        "start_weight": "StartWeight", "current_weight": "CurrentWeight",
        "days": "Days", "feed_used": "FeedUsed",
        "market_price": "MarketPrice", "feed_price": "FeedPrice",
        "adg": "ADG", "profit": "Profit", "methane": "CH4", "fcr": "FCR", "timestamp": "Timestamp"
    })
db_norm = normalize_df(db_df.copy())

# Tabs for session and DB
tab1, tab2, tab3 = st.tabs(["Session Records", "DB Records", "Benchmarking visuals"])

with tab1:
    st.subheader("Session Records (volatile)")
    if not session_norm.empty:
        st.dataframe(session_norm, use_container_width=True)
        st.download_button("Download session CSV", data=session_norm.to_csv(index=False).encode("utf-8"),
                           file_name="session_records.csv", mime="text/csv")
        if st.button("Save session → DB (from tab)"):
            save_records_to_db(session_norm.to_dict(orient="records"))
            st.success("Saved session records to DB.")
    else:
        st.info("No session records. Add some in the sidebar.")

with tab2:
    st.subheader("Database Records (persistent)")
    if not db_norm.empty:
        st.dataframe(db_norm, use_container_width=True)
        st.download_button("Download DB CSV", data=db_norm.to_csv(index=False).encode("utf-8"),
                           file_name="db_records.csv", mime="text/csv")

        # allow deletion of selected animal IDs
        ids = db_norm["ID"].fillna("").astype(str).tolist()
        to_delete = st.multiselect("Select animal IDs to DELETE from DB", options=ids)
        if st.button("Delete selected from DB"):
            if to_delete:
                delete_db_records_by_ids(to_delete)
                st.success(f"Deleted {len(to_delete)} record(s) from DB.")
            else:
                st.info("No IDs selected.")
    else:
        st.info("No records in DB yet. Save session records to persist.")

with tab3:
    st.subheader("Per-species Benchmarking — ADG vs Species Targets")
    # Use combined df (prefer DB + session)
    combined = pd.concat([db_norm, session_norm], ignore_index=True)
    combined = combined.dropna(subset=["ADG", "Species"])
    if combined.empty:
        st.info("No ADG data available. Add records (session or DB) to view benchmarking visuals.")
    else:
        # Boxplot (ADG distribution) per species with a rule at adg_min
        box = alt.Chart(combined).mark_boxplot(size=40).encode(
            x=alt.X("Species:N", title="Species"),
            y=alt.Y("ADG:Q", title="ADG (kg/day)"),
            color=alt.Color("Species:N", legend=None)
        ).properties(width=600, height=300)

        # Create a small dataframe for species rules
        rules = pd.DataFrame([
            {"Species": s, "adg_min": v["adg_min"]} for s, v in SPECIES_INFO.items()
        ])
        rule_layer = alt.Chart(rules).mark_rule(strokeDash=[4,4], color="red").encode(
            y="adg_min:Q",
            x=alt.X("Species:N", title="Species")
        )
        rule_text = alt.Chart(rules).mark_text(dx=5, dy=-10, color="red").encode(
            x=alt.X("Species:N"),
            y=alt.Y("adg_min:Q"),
            text=alt.Text("adg_min:Q", format=".2f")
        )

        st.altair_chart((box + rule_layer + rule_text).configure_axis(labelFontSize=12, titleFontSize=13), use_container_width=True)

        st.markdown("---")
        st.subheader("ADG vs Profit (scatter) — target ADG shown per species")
        scatter = alt.Chart(combined).mark_circle(size=120).encode(
            x=alt.X("ADG:Q", title="ADG (kg/day)"),
            y=alt.Y("Profit:Q", title="Profit (KES)"),
            color=alt.Color("Species:N"),
            tooltip=["ID", "Species", alt.Tooltip("ADG:Q", format=".4f"), alt.Tooltip("Profit:Q", format=",.2f"), alt.Tooltip("FCR:Q", format=".3f")]
        ).properties(height=400)

        # add horizontal lines for adg_min across the plot area (one per species)
        # we'll map adg_min values to a single vertical rule dataset and draw them spanning the chart using transform_filter
        # but simpler: add rule layer with y=adg_min and color based on species (semi-transparent)
        rules_all = rules.copy()
        rules_all["label"] = rules_all["adg_min"].apply(lambda v: f"Target {v:.2f} ADG")
        rule_scatter = alt.Chart(rules_all).mark_rule(strokeDash=[6,6], color="gray").encode(
            y="adg_min:Q",
            size=alt.value(1)
        )
        st.altair_chart((scatter + rule_scatter).interactive(), use_container_width=True)

st.markdown("----")
st.caption("Developed for UoN Animal Production Research | Persistent storage: local SQLite")
