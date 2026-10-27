"""PrivacyLens — dark, multi-page privacy intelligence dashboard."""
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from src.detector import PrivacyLens
from src.redactor import RedactionStrategy
from src.patterns import ENTITY_META, list_supported_entities

st.set_page_config(page_title="PrivacyLens | Privacy Intelligence", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# ---- Dark enterprise styling ----
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #080d18; color: #e5eaf4; }
[data-testid="stHeader"] { background: rgba(8,13,24,.92); }
[data-testid="stSidebar"] { background: #0c1424; border-right: 1px solid #1e2b42; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }
h1,h2,h3 { color: #f3f6fc !important; letter-spacing: -.02em; }
p, label, [data-testid="stMarkdownContainer"] { color: #c2ccdc; }
[data-testid="stMetric"] { background: linear-gradient(135deg,#111d31,#0e1728); border: 1px solid #24334b; padding: 16px 18px; border-radius: 14px; }
[data-testid="stMetricLabel"] { color: #91a3bd !important; }
[data-testid="stMetricValue"] { color: #f4f7ff !important; }
div.stButton > button, div.stDownloadButton > button { border-radius: 9px; border: 1px solid #2b3c56; min-height: 2.6rem; }
div.stButton > button[kind="primary"] { background: #3b82f6; border-color: #3b82f6; color: white; }
.pl-card { background: linear-gradient(145deg,#111d30,#0d1626); border: 1px solid #24334a; border-radius: 14px; padding: 18px 20px; margin-bottom: 10px; }
.pl-muted { color: #8ea1bb; font-size: .88rem; }
.pl-kicker { color: #60a5fa; text-transform: uppercase; font-size: .72rem; letter-spacing: .14em; font-weight: 700; }
.pl-pill { display:inline-block; padding:4px 9px; border-radius:99px; background:#172b46; border:1px solid #2a4568; color:#a8caff; font-size:.75rem; }
hr { border-color: #24334a; }
[data-testid="stDataFrame"] { border: 1px solid #24334a; border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_detector():
    return PrivacyLens(use_spacy=True, spacy_model="en_core_web_sm")

detector = get_detector()
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

SAMPLES = {
    "Customer Support Ticket": "Hi team, customer Rahul Sharma (rahul.sharma92@gmail.com, +91-98765-43210) is unable to login. His Aadhaar ending with 9012 and PAN ABCDE1234F were verified earlier. Card number 4532 0148 7932 1142 was used for payment. Please check from IP 103.25.44.18.",
    "Medical Note": "Patient: Priya Patel, DOB 12/03/1988. Contact: 98200 12345. Aadhaar: 2345-6789-0123. Diagnosis discussed in confidence. Follow-up scheduled.",
    "Internal Email": "From: ananya.i@company.com\nPlease share the employee ID EMP-004821 details with finance. Also note the UPI id ananya@okhdfcbank for reimbursement.",
    "Clean Text": "The weather is nice today and the meeting starts at 3 PM.",
}

# Sidebar navigation and global settings
with st.sidebar:
    st.markdown("<div style='font-size:1.55rem;font-weight:800;color:#f4f7ff'>🛡️ PrivacyLens</div><div class='pl-muted'>PRIVACY INTELLIGENCE PLATFORM</div>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("WORKSPACE", ["Overview", "Scan & Redact", "Scan History", "Entity Intelligence", "Platform & API"], label_visibility="visible", key="page")
    st.markdown("---")
    st.markdown("**Detection controls**")
    strategy = st.selectbox("Redaction strategy", [s.value for s in RedactionStrategy], index=0)
    confidence = st.slider("Minimum confidence", 0.0, 1.0, 0.5, 0.05)
    show_redacted = st.toggle("Generate redacted output", value=True)
    detector.confidence_threshold = confidence
    st.markdown("---")
    st.markdown("<span class='pl-pill'>● LOCAL DEMO</span>", unsafe_allow_html=True)
    st.caption("Scans are stored in this browser session only. Do not paste real sensitive data into a demo environment.")

# Header
st.markdown("<div class='pl-kicker'>SECURITY WORKSPACE / PERSONAL DATA PROTECTION</div>", unsafe_allow_html=True)
st.title({"Overview":"Privacy operations overview", "Scan & Redact":"Scan and redact content", "Scan History":"Scan activity", "Entity Intelligence":"Entity intelligence", "Platform & API":"Platform and API"}[page])
st.markdown("Monitor potential exposure, inspect detected entities, and produce redacted text from one workspace.")

# Small reusable helpers
def risk_color(level):
    return {"critical":"#fb7185", "high":"#fb923c", "medium":"#facc15", "low":"#34d399"}.get(str(level).lower(), "#94a3b8")

def render_stat(label, value, help_text=None):
    st.metric(label, value, help=help_text)

def run_scan(text, label="Manual scan"):
    result = detector.analyze(text, redact=show_redacted, strategy=RedactionStrategy(strategy))
    record = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": label, "characters": len(text), "entities": result.entity_count, "risk": result.risk_level, "score": float(result.risk_score), "summary": result.summary, "redacted": result.redacted_text, "input": text, "entity_rows": [{"Type":e.entity_type,"Text":e.text,"Category":e.category,"Risk":e.risk,"Confidence":round(float(e.score),2),"Source":e.source,"Position":f"{e.start}-{e.end}"} for e in result.entities]}
    st.session_state.scan_history.insert(0, record)
    st.session_state.last_result = record
    return record

if page == "Overview":
    history = st.session_state.scan_history
    total_scans = len(history)
    total_entities = sum(x["entities"] for x in history)
    high_risk = sum(1 for x in history if x["risk"] in ("high", "critical"))
    avg_score = sum(x["score"] for x in history) / total_scans if total_scans else 0
    a,b,c,d = st.columns(4)
    with a: render_stat("Scans this session", total_scans)
    with b: render_stat("Entities detected", total_entities)
    with c: render_stat("High / critical scans", high_risk)
    with d: render_stat("Average risk score", f"{avg_score:.2f}")
    st.markdown("### Workspace snapshot")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("<div class='pl-card'><div class='pl-kicker'>QUICK ACTION</div><h3>Inspect content before sharing</h3><p>Run a sample or paste text to identify supported personal and sensitive data, review risk, and redact findings.</p></div>", unsafe_allow_html=True)
        if st.button("Open Scan & Redact →", type="primary", use_container_width=True):
            st.session_state["page"] = "Scan & Redact"
            st.rerun()
        st.markdown("### Recent scans")
        if history:
            st.dataframe(pd.DataFrame([{ "Time":x["time"],"Source":x["source"],"Entities":x["entities"],"Risk":x["risk"].upper(),"Score":round(x["score"],2)} for x in history[:8]]), use_container_width=True, hide_index=True)
        else:
            st.info("No scans yet. Open Scan & Redact to run your first analysis. Results will appear here for this session.")
    with right:
        st.markdown("### Risk distribution")
        if history:
            counts = pd.Series([x["risk"].title() for x in history]).value_counts()
            st.bar_chart(counts)
        else:
            st.markdown("<div class='pl-card'><h3>Awaiting scan data</h3><p class='pl-muted'>Risk analytics will populate after you run scans.</p></div>", unsafe_allow_html=True)
        st.markdown("### Detection coverage")
        entities = list_supported_entities()
        st.metric("Supported entity types", len(entities))
        st.caption("Coverage depends on configured patterns, spaCy model behavior, and the selected confidence threshold.")

elif page == "Scan & Redact":
    st.markdown("<div class='pl-card'><span class='pl-pill'>TEXT ANALYSIS</span><p class='pl-muted'>Use sample data to explore the interface. Avoid entering real customer, patient, or identity information.</p></div>", unsafe_allow_html=True)
    sample = st.selectbox("Start with a sample", ["Choose a sample..."] + list(SAMPLES.keys()))
    initial = SAMPLES.get(sample, "")
    text_input = st.text_area("Content to scan", value=initial, height=190, placeholder="Paste text here…", key="scan_input")
    x,y,z = st.columns([1,1,5])
    with x: analyze = st.button("Analyze content", type="primary", use_container_width=True)
    with y: clear = st.button("Clear input", use_container_width=True)
    if clear:
        st.session_state.scan_input = ""
        st.rerun()
    if analyze:
        if not text_input.strip():
            st.warning("Enter some text or select a sample first.")
        else:
            with st.spinner("Inspecting content for supported sensitive entities…"):
                run_scan(text_input, sample if sample != "Choose a sample..." else "Manual scan")
    result = st.session_state.last_result
    if result:
        st.markdown("---")
        st.markdown("### Analysis result")
        a,b,c,d = st.columns(4)
        with a: render_stat("Risk score", f"{result['score']:.2f}")
        with b: render_stat("Risk level", result["risk"].upper())
        with c: render_stat("Entities found", result["entities"])
        with d: render_stat("Characters scanned", f"{result['characters']:,}")
        st.markdown(f"<div class='pl-card'><span style='color:{risk_color(result['risk'])};font-weight:800'>● {result['risk'].upper()} RISK</span><p>{result['summary']}</p></div>", unsafe_allow_html=True)
        if result["entity_rows"]:
            st.markdown("#### Detected entities")
            st.dataframe(pd.DataFrame(result["entity_rows"]), use_container_width=True, hide_index=True)
        else:
            st.success("No sensitive information was detected by the configured detectors.")
        if result["redacted"] is not None:
            st.markdown("#### Sanitized output")
            st.code(result["redacted"], language=None)
            st.download_button("Download redacted text", data=result["redacted"], file_name="privacy_lens_redacted.txt", mime="text/plain")
        with st.expander("Show original input"):
            st.text(result["input"])

elif page == "Scan History":
    history = st.session_state.scan_history
    if not history:
        st.info("Your session history is empty. Run a scan first; records are held in Streamlit session state and are not a permanent audit database.")
    else:
        f1, f2 = st.columns([2,1])
        with f1: query = st.text_input("Filter by source or risk", placeholder="e.g. medical, high, manual")
        with f2: show_count = st.selectbox("Rows", [10,25,50], index=0)
        rows = [{"Time":x["time"],"Source":x["source"],"Characters":x["characters"],"Entities":x["entities"],"Risk":x["risk"].upper(),"Risk score":round(x["score"],2),"Summary":x["summary"]} for x in history]
        df = pd.DataFrame(rows)
        if query:
            mask = df.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
            df = df[mask]
        st.dataframe(df.head(show_count), use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Export visible history as CSV", data=csv, file_name="privacy_lens_session_history.csv", mime="text/csv")
        selected = st.selectbox("Inspect a scan", options=list(range(len(history))), format_func=lambda i: f"{history[i]['time']} · {history[i]['source']} · {history[i]['risk'].upper()}")
        item = history[selected]
        st.markdown("#### Scan details")
        st.write(item["summary"])
        if item["entity_rows"]: st.dataframe(pd.DataFrame(item["entity_rows"]), use_container_width=True, hide_index=True)
        if st.button("Clear session history"):
            st.session_state.scan_history = []
            st.session_state.last_result = None
            st.rerun()

elif page == "Entity Intelligence":
    st.markdown("Explore the entity types configured in the existing detection engine. Metadata describes the project's current labels; detection coverage is not a guarantee of perfect recognition.")
    supported = list_supported_entities()
    rows = []
    for entity_type in supported:
        meta = ENTITY_META.get(entity_type, {})
        rows.append({"Entity type":entity_type,"Category":meta.get("category", "—"),"Risk":meta.get("risk", "medium").upper(),"Description":meta.get("description", "Configured detector entity")})
    df = pd.DataFrame(rows)
    if not df.empty:
        f1,f2 = st.columns([2,1])
        with f1: q = st.text_input("Search entity types", placeholder="Search e.g. EMAIL, PHONE, PAN")
        with f2: risk_filter = st.selectbox("Risk category", ["All"] + sorted(df["Risk"].unique().tolist()))
        if q: df = df[df.astype(str).apply(lambda col: col.str.contains(q, case=False, na=False)).any(axis=1)]
        if risk_filter != "All": df = df[df["Risk"] == risk_filter]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(df)} configured entity type(s).")
    else:
        st.warning("No entity metadata was returned by the current detector configuration.")

else:  # Platform & API
    st.markdown("### Service endpoints")
    st.markdown("<div class='pl-card'><div class='pl-kicker'>STREAMLIT FRONTEND</div><h3>Local web workspace</h3><p class='pl-muted'>The UI runs in your local Python environment. Keep the terminal process running while you use it.</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='pl-card'><div class='pl-kicker'>FASTAPI BACKEND</div><h3>Interactive API documentation</h3><p>Start the API in a second terminal from the project root:</p><code>uvicorn src.api:app --reload --port 8000</code><p>Then open <a href='http://localhost:8000/docs' target='_blank'>http://localhost:8000/docs</a>.</p></div>", unsafe_allow_html=True)
    st.markdown("### Current configuration")
    c1,c2,c3 = st.columns(3)
    with c1: render_stat("Redaction strategy", strategy)
    with c2: render_stat("Confidence threshold", f"{confidence:.2f}")
    with c3: render_stat("Redacted output", "Enabled" if show_redacted else "Disabled")
    st.markdown("### Notes and limitations")
    st.warning("This is a portfolio/demo application, not a certified compliance tool. Detector results can include false positives and missed entities. Validate outputs before relying on them for real decisions.")
    st.markdown("- History is session-only and clears when the session resets.\n- The current app analyzes text; this UI upgrade does not add PDF/DOCX ingestion or new detection models.\n- Redaction is only as reliable as the configured detection rules and NLP model.")

st.markdown("---")
st.markdown("<div class='pl-muted'>PRIVACYLENS · DARK SECURITY WORKSPACE · LOCAL DEMO · Existing detection engine preserved</div>", unsafe_allow_html=True)
