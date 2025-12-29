import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF
import sqlite3
import io
from math import inf
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="AEGIS Livestock Pro", page_icon="🧬", layout="wide")

# --- 2. INITIALIZE SESSION STATE (in-memory DB for the session) ---
if "animal_records" not in st.session_state:
    st.session_state.animal_records = []

# --- 3. SPECIES BENCHMARKS ---
SPECIES_INFO = {
    "Beef": {"target": 450.0, "adg": 0.8, "icon": "🐂", "ch4": 0.18},
    "Pig": {"target": 130.0, "adg": 0.6, "icon": "🐖", "ch4": 0.04},
    "Broiler": {"target": 2.5, "adg": 0.05, "icon": "🐥", "ch4": 0.002},
}

DB_PATH = "livestock_runs.db"

# --- 4. HELPERS ---
def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return None

def create_pdf_bytes(records):
    """Return PDF as bytes (binary) for download."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "AEGIS Livestock Analytics - Production Report", ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(6)

    # Table header
    col_names = ["Animal ID", "Species", "ADG (kg/day)", "Profit (KES)", "Methane (kg)", "Weight (kg)"]
    widths = [35, 30, 30, 35, 35, 30]
    pdf.set_fill_color(220, 230, 255)
    pdf.set_font("Arial", "B", 9)
    for name, w in zip(col_names, widths):
        pdf.cell(w, 8, name, 1, 0, "C", True)
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for r in records:
        pdf.cell(widths[0], 7, str(r.get("ID", ""))[:18], 1)
        pdf.cell(widths[1], 7, str(r.get("Species", "")), 1)
        pdf.cell(widths[2], 7, f"{r.get('ADG', 0):.2f}" if r.get("ADG") is not None else "—", 1, 0, "R")
        pdf.cell(widths[3], 7, f"{r.get('Profit', 0):,.0f}", 1, 0, "R")
        pdf.cell(widths[4], 7, f"{r.get('Methane', 0):.2f}", 1, 0, "R")
        pdf.cell(widths[5], 7, f"{r.get('Weight', 0):.1f}", 1, 1, "R")

    return pdf.output(dest="S").encode("latin-1")

def init_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        animal_id TEXT,
        species TEXT,
        weight REAL,
        adg REAL,
        profit REAL,
        methane REAL
    )
    """)
    conn.commit()
    conn.close()

def save_records_to_db(records, path=DB_PATH):
    init_db(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    rows = []
    for r in records:
        rows.append((
            datetime.utcnow().isoformat(),
            r.get("ID"),
            r.get("Species"),
            float(r.get("Weight", 0)),
            float(r.get("ADG", 0)) if r.get("ADG") is not None else None,
            float(r.get("Profit", 0)),
            float(r.get("Methane", 0)),
        ))
    cur.executemany("""
        INSERT INTO runs (timestamp, animal_id, species, weight, adg, profit, methane)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    conn.close()

def load_db_records(path=DB_PATH, limit=500):
    try:
        conn = sqlite3.connect(path)
        df = pd.read_sql_query(f"SELECT * FROM runs ORDER BY id DESC LIMIT {limit}", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# --- 5. UI HEADER ---
st.title("🐄 AEGIS Livestock Analytics Pro")
st.caption("University of Nairobi | Animal Production Department | Smart-Farm Edition")

# --- 6. INPUT FORM (Batch Input) in sidebar ---
with st.sidebar:
    st.header("🧬 New Animal Entry / Bulk Upload")

    # Single entry form
    with st.form("entry_form", clear_on_submit=True):
        animal_id = st.text_input("Animal Tag ID", value=f"TAG-{len(st.session_state.animal_records)+1}")
        spec = st.selectbox("Species", list(SPECIES_INFO.keys()))
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            wt_start = st.number_input("Start Weight (kg)", 0.0, 10000.0, 250.0, step=0.1)
            wt_curr = st.number_input("Current Weight (kg)", 0.0, 10000.0, 300.0, step=0.1)
        with col_in2:
            period = st.number_input("Days", 1, 3650, 30)
            feed = st.number_input("Feed Used (kg)", 0.0, 100000.0, 400.0, step=0.1)

        m_price = st.number_input("Market Price (KES/kg)", value=210.0, step=1.0)
        f_price = st.number_input("Feed Price (KES/kg)", value=45.0, step=0.1)

        submit = st.form_submit_button("➕ Add to Session")

        if submit:
            if wt_curr > wt_start:
                gain = wt_curr - wt_start
                adg = safe_div(gain, period)
                # incremental profit for the period (value of gain minus feed cost)
                profit_inc = (gain * m_price) - (feed * f_price)
                # also compute gross current value and net after feed cost if useful
                gross_current_value = (wt_curr * m_price)
                methane = period * SPECIES_INFO[spec]["ch4"]
                record = {
                    "ID": animal_id,
                    "Species": spec,
                    "ADG": round(adg, 4) if adg is not None else None,
                    "Profit": profit_inc,
                    "GrossValue": gross_current_value,
                    "Methane": methane,
                    "Weight": wt_curr,
                    "Timestamp": datetime.utcnow().isoformat(),
                }
                st.session_state.animal_records.append(record)
                st.success(f"Record for {animal_id} saved to session.")
            else:
                st.error("Current weight must be greater than start weight.")

    # Bulk CSV upload (optional)
    st.markdown("---")
    st.write("Bulk import CSV: columns -> ID, Species, StartWeight, CurrentWeight, Days, FeedUsed, MarketPrice, FeedPrice")
    csv_file = st.file_uploader("Upload CSV to add multiple records", type=["csv"])
    if csv_file is not None:
        try:
            bulk_df = pd.read_csv(csv_file)
            added = 0
            for _, row in bulk_df.iterrows():
                try:
                    aid = str(row.get("ID", f"TAG-{len(st.session_state.animal_records)+1}"))
                    species = row.get("Species", list(SPECIES_INFO.keys())[0])
                    start = float(row.get("StartWeight", 0))
                    curr = float(row.get("CurrentWeight", 0))
                    days = int(row.get("Days", 1))
                    feed_used = float(row.get("FeedUsed", 0))
                    mpr = float(row.get("MarketPrice", m_price))
                    fpr = float(row.get("FeedPrice", f_price))
                    if curr > start and species in SPECIES_INFO:
                        gain = curr - start
                        adg = safe_div(gain, days)
                        profit_inc = (gain * mpr) - (feed_used * fpr)
                        methane = days * SPECIES_INFO[species]["ch4"]
                        st.session_state.animal_records.append({
                            "ID": aid,
                            "Species": species,
                            "ADG": round(adg, 4) if adg is not None else None,
                            "Profit": profit_inc,
                            "GrossValue": curr * mpr,
                            "Methane": methane,
                            "Weight": curr,
                            "Timestamp": datetime.utcnow().isoformat(),
                        })
                        added += 1
                except Exception:
                    continue
            st.success(f"Imported {added} records from CSV.")
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")

    st.markdown("---")
    if st.button("Save session records to local DB"):
        if st.session_state.animal_records:
            try:
                save_records_to_db(st.session_state.animal_records)
                st.success("Saved session records to local SQLite DB.")
            except Exception as e:
                st.error(f"Failed to save to DB: {e}")
        else:
            st.info("No records in session to save.")

# --- 7. DASHBOARD & COMPARISON ---
if st.session_state.animal_records:
    df = pd.DataFrame(st.session_state.animal_records)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Herd Profit (period)", f"KES {df['Profit'].sum():,.0f}")
    c2.metric("Avg ADG", f"{df['ADG'].dropna().mean():.2f} kg/day" if not df['ADG'].dropna().empty else "—")
    c3.metric("Total CH₄ Emitted (period)", f"{df['Methane'].sum():.2f} kg")
    c4.metric("Animals Tracked", f"{len(df)}")

    st.markdown("---")
    # Allow deletion of selected records by ID
    st.subheader("📋 Herd Comparison Table")
    st.dataframe(df.assign(Timestamp=df.get("Timestamp", "")).loc[:, ["ID", "Species", "Weight", "ADG", "Profit", "Methane", "Timestamp"]], use_container_width=True)

    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.write("Select records to remove (by Animal ID):")
        ids = [str(x) for x in df["ID"].tolist()]
        to_remove = st.multiselect("Remove IDs", options=ids)
    with cols[1]:
        if st.button("Delete selected"):
            if to_remove:
                st.session_state.animal_records = [r for r in st.session_state.animal_records if r["ID"] not in to_remove]
                st.success(f"Removed {len(to_remove)} record(s).")
                st.experimental_rerun()
            else:
                st.info("No IDs selected.")
    with cols[2]:
        if st.button("Clear all records"):
            st.session_state.animal_records = []
            st.experimental_rerun()

    # Scatter chart Performance vs Sustainability
    st.markdown("---")
    st.subheader("📊 Performance vs Sustainability")
    chart = alt.Chart(df).mark_circle(size=120).encode(
        x=alt.X("ADG:Q", title="ADG (kg/day)"),
        y=alt.Y("Profit:Q", title="Profit (KES)"),
        color="Species:N",
        tooltip=["ID", "Species", alt.Tooltip("ADG:Q", format=".3f"), alt.Tooltip("Profit:Q", format=",.0f"), alt.Tooltip("Methane:Q", format=".2f")]
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    # --- PDF & CSV EXPORT ---
    st.markdown("---")
    st.subheader("Export reports")
    if st.button("Generate PDF production report (download below)"):
        try:
            pdf_bytes = create_pdf_bytes(st.session_state.animal_records)
            st.success("PDF generated — use the download button below.")
            st.download_button("Download PDF report", data=pdf_bytes, file_name="Production_Report.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Failed to generate PDF: {e}")

    # CSV download (session data)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download session data (CSV)", data=csv_bytes, file_name="herd_session.csv", mime="text/csv")

    # Option to view DB records saved earlier
    st.markdown("---")
    if st.button("Load recent records from local DB"):
        df_db = load_db_records()
        if not df_db.empty:
            st.subheader("Records from local DB")
            st.dataframe(df_db, use_container_width=True)
        else:
            st.info("No DB records found or DB empty.")
else:
    st.info("👋 Welcome! Use the sidebar to add your first animal record (or upload a CSV) to build your herd report.")
