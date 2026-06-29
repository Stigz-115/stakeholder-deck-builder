"""
Stakeholder Deck Builder — generate persona-specific briefing PDFs for every
member of a healthcare buying committee, from a single form.
"""

import os
import streamlit as st
from scanner.deck_builder import generate_brief, generate_all_zip, _calc_roi, PERSONAS, STATE_LAWS

st.set_page_config(
    page_title="Stakeholder Deck Builder — Freshpaint",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Suppress Streamlit Cloud's injected sidebar nav and collapse toggle globally
st.markdown("""
<style>
div[data-testid="stSidebarNav"],
section[data-testid="stSidebar"] nav,
button[data-testid="collapsedControl"],
button[data-testid="stSidebarCollapseButton"],
button[aria-label="Close sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="open sidebar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Password gate ─────────────────────────────────────────────────────────────
_APP_PASSWORD = os.environ.get("APP_PASSWORD", "freshpaint")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { background-color: #05080F !important; color: #E8EDF5 !important; }
    .stApp { background: #05080F; }
    #MainMenu, header[data-testid="stHeader"], footer { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-family:Syne,sans-serif;font-size:0.65rem;font-weight:700;"
            "letter-spacing:0.3em;text-transform:uppercase;color:rgba(0,255,178,0.6);"
            "text-align:center;margin-bottom:0.5rem'>Freshpaint</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;"
            "text-align:center;color:#E8EDF5;margin-bottom:0.25rem'>Stakeholder Deck Builder</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
            "text-align:center;color:rgba(232,237,245,0.35);margin-bottom:2rem'>Enter access password</div>",
            unsafe_allow_html=True,
        )
        pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                            placeholder="Enter password…")
        if st.button("→  Continue", use_container_width=True):
            if pwd == _APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Mono', monospace;
    background-color: #05080F !important;
    color: #E8EDF5 !important;
}
.stApp { background: #05080F; }
.stApp::before {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(0,255,178,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,178,0.025) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none; z-index: 0;
}
#MainMenu, header[data-testid="stHeader"], footer { display: none !important; }
.block-container { padding-top: 0 !important; max-width: 1100px !important; }

/* ── Hero ── */
.deck-hero {
    background: linear-gradient(135deg, #05080F 0%, #0B1628 50%, #05080F 100%);
    border-bottom: 1px solid rgba(0,255,178,0.15);
    padding: 2.8rem 2rem 2.2rem;
    margin: 0 -4rem 2.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.deck-hero::before {
    content: '';
    position: absolute; top: -60px; left: 50%; transform: translateX(-50%);
    width: 500px; height: 200px;
    background: radial-gradient(ellipse, rgba(0,255,178,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.fp-wordmark {
    font-family: 'Syne', sans-serif; font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.35em; text-transform: uppercase;
    color: rgba(0,255,178,0.6); margin-bottom: 0.6rem;
}
.deck-hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.1rem); font-weight: 800;
    line-height: 1.1; margin: 0 0 0.6rem; color: #E8EDF5; letter-spacing: -0.02em;
}
.deck-hero h1 span { color: #00FFB2; }
.deck-hero p {
    font-size: 0.83rem; color: rgba(232,237,245,0.5);
    max-width: 580px; margin: 0 auto; line-height: 1.7;
}

/* ── Form panel ── */
.form-section {
    font-family: 'Syne', sans-serif; font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.3em; text-transform: uppercase;
    color: rgba(0,255,178,0.6);
    border-bottom: 1px solid rgba(0,255,178,0.1);
    padding-bottom: 0.5rem; margin: 1.5rem 0 1rem;
}

/* ── Input overrides ── */
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stSlider"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: rgba(232,237,245,0.45) !important;
}
.stTextInput input, .stNumberInput input {
    background: rgba(5,8,15,0.9) !important;
    border: 1px solid rgba(0,255,178,0.2) !important;
    border-radius: 3px !important;
    color: #E8EDF5 !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: rgba(5,8,15,0.9) !important;
    border: 1px solid rgba(0,255,178,0.2) !important;
    border-radius: 3px !important;
}

/* ── Generate button ── */
.stButton > button {
    background: #00FFB2 !important;
    color: #05080F !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 3px !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #00E5A0 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(0,255,178,0.25) !important;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    background: transparent !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    padding: 0.7rem 1.2rem !important;
    transition: all 0.15s !important;
    width: 100%;
}

/* ── Persona cards (preview) ── */
.persona-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin: 1.5rem 0;
}
.persona-card {
    background: rgba(12,22,42,0.8);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 4px;
    padding: 1.1rem 1.2rem;
    position: relative;
    overflow: hidden;
}
.persona-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0; width: 3px;
    border-radius: 4px 0 0 4px;
}
.pc-cmo::before  { background: #00C896; }
.pc-cfo::before  { background: #E8630A; }
.pc-gc::before   { background: #D42B4A; }
.pc-cto::before  { background: #1A8BFF; }

.pc-badge {
    display: inline-block;
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; padding: 0.15rem 0.5rem;
    border-radius: 2px; margin-bottom: 0.4rem;
}
.pc-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem; font-weight: 700;
    color: #E8EDF5; margin-bottom: 0.3rem;
}
.pc-focus {
    font-size: 0.68rem; color: rgba(232,237,245,0.4);
    margin-bottom: 0.5rem; letter-spacing: 0.03em;
}
.pc-bullets {
    font-size: 0.7rem; color: rgba(232,237,245,0.55);
    line-height: 1.7;
}

/* ── Download panel ── */
.download-panel {
    background: rgba(12,22,42,0.8);
    border: 1px solid rgba(0,255,178,0.2);
    border-radius: 4px;
    padding: 1.8rem;
    margin-top: 1.5rem;
}
.dp-title {
    font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 800;
    color: #E8EDF5; margin-bottom: 0.3rem;
}
.dp-sub {
    font-size: 0.72rem; color: rgba(232,237,245,0.4);
    margin-bottom: 1.2rem; line-height: 1.6;
}

/* ── ROI preview strip ── */
.roi-strip {
    display: flex; gap: 0.5rem; margin: 1rem 0; flex-wrap: wrap;
}
.roi-chip {
    flex: 1; min-width: 100px;
    background: rgba(12,22,42,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 3px; padding: 0.7rem; text-align: center;
}
.roi-chip-num {
    font-family: 'Syne', sans-serif; font-size: 1.2rem; font-weight: 800;
    color: #00FFB2; line-height: 1; margin-bottom: 0.2rem;
}
.roi-chip-label {
    font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: rgba(232,237,245,0.3);
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="deck-hero">
  <div class="fp-wordmark">Freshpaint · Sales Enablement</div>
  <h1>Stakeholder <span>Deck Builder</span></h1>
  <p>
    Fill in one form. Get four tailored briefing documents — one for every member of
    the buying committee. Each PDF speaks to that stakeholder's specific concerns,
    personalized with the prospect's name, spend, and states served.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Persona preview grid ──────────────────────────────────────────────────────
PREVIEW = {
    "cmo": {
        "color": "#00C896", "title": "CMO Brief",
        "focus": "Marketing Performance & Analytics",
        "bullets": "ROAS degradation impact · Attribution loss · Remarketing ROI · Performance benchmarks",
    },
    "cfo": {
        "color": "#E8630A", "title": "CFO Brief",
        "focus": "Financial Risk & ROI",
        "bullets": "OCR fine exposure · Settlement data · ROI calculation · Payback period",
    },
    "gc": {
        "color": "#D42B4A", "title": "GC / CCO Brief",
        "focus": "Legal & Regulatory Compliance",
        "bullets": "HHS OCR timeline · Enforcement cases · State laws · Defensible position",
    },
    "cto": {
        "color": "#1A8BFF", "title": "CTO / IT Brief",
        "focus": "Technical Implementation & Security",
        "bullets": "Architecture diagram · Implementation steps · SOC 2 · Integration list",
    },
}

cards_html = '<div class="persona-grid">'
for key, p in PREVIEW.items():
    cards_html += f"""
    <div class="persona-card pc-{key}">
      <div class="pc-badge" style="background:{p['color']}22;color:{p['color']};
           border:1px solid {p['color']}44">{key.upper()}</div>
      <div class="pc-title">{p['title']}</div>
      <div class="pc-focus">{p['focus']}</div>
      <div class="pc-bullets">{p['bullets']}</div>
    </div>"""
cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)

# ── Form ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="form-section">Prospect Details</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    company = st.text_input("Prospect company name", placeholder="Baptist Health")
    org_type = st.selectbox("Organization type", [
        "Hospital / Health System", "Digital Health / DTC",
        "Telehealth", "Specialty Practice / Group", "Payer / Insurance",
    ])
with col2:
    monthly_spend = st.number_input(
        "Monthly ad spend ($)", min_value=5_000, max_value=5_000_000,
        value=75_000, step=5_000,
    )
    freshpaint_cost = st.number_input(
        "Freshpaint annual quote ($)", min_value=15_000, max_value=300_000,
        value=40_000, step=5_000,
    )

st.markdown('<div class="form-section">Geography & Exposure</div>', unsafe_allow_html=True)

all_states = sorted(STATE_LAWS.keys())
states = st.multiselect(
    "States where org serves patients (for state law mapping in GC brief)",
    options=all_states,
    default=["TX", "CA", "FL"],
    help="Select all states where the prospect has significant patient volume",
)

st.markdown('<div class="form-section">Sales Rep Details</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    rep_name  = st.text_input("Your name", placeholder="Alex Smith")
with col4:
    rep_email = st.text_input("Your email", placeholder="alex@freshpaint.io")

# ── Live ROI preview ──────────────────────────────────────────────────────────
if monthly_spend and org_type:
    m = _calc_roi(monthly_spend, org_type, freshpaint_cost)
    payback_str = f"{m['payback']:.1f} mo"
    chips = [
        (f"${m['total']:,.0f}", "Annual dark cost"),
        (f"{m['roi']:.1f}x",   "Freshpaint ROI"),
        (payback_str,          "Payback period"),
        (f"${m['total'] - freshpaint_cost:,.0f}", "Net savings"),
    ]
    chips_html = '<div class="roi-strip">'
    for num, label in chips:
        chips_html += f"""
        <div class="roi-chip">
          <div class="roi-chip-num">{num}</div>
          <div class="roi-chip-label">{label}</div>
        </div>"""
    chips_html += "</div>"
    st.markdown(
        '<div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;'
        'color:rgba(0,255,178,0.5);margin-top:0.5rem">ROI Preview (used in CMO & CFO briefs)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(chips_html, unsafe_allow_html=True)

# ── Generate ──────────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
generate = st.button("Generate All Four Briefs →", use_container_width=False)

if generate:
    if not company.strip():
        st.warning("Enter a company name to personalize the briefs.")
    else:
        data = {
            "company":        company.strip(),
            "org_type":       org_type,
            "monthly_spend":  monthly_spend,
            "freshpaint_cost": freshpaint_cost,
            "states":         states,
            "rep_name":       rep_name.strip() or "Your Freshpaint AE",
            "rep_email":      rep_email.strip() or "sales@freshpaint.io",
        }
        data["metrics"] = _calc_roi(monthly_spend, org_type, freshpaint_cost)

        with st.spinner("Generating briefs..."):
            try:
                briefs = {k: generate_brief(k, data) for k in ("cmo", "cfo", "gc", "cto")}
                zip_bytes = generate_all_zip(data)
                st.session_state["briefs"]    = briefs
                st.session_state["zip_bytes"] = zip_bytes
                st.session_state["brief_company"] = company.strip()
            except Exception as e:
                st.error(f"Generation error: {e}")

# ── Download panel ────────────────────────────────────────────────────────────
if "briefs" in st.session_state:
    briefs  = st.session_state["briefs"]
    slug    = st.session_state["brief_company"].lower().replace(" ", "_")
    company_display = st.session_state["brief_company"]

    st.html(f"""
    <div class="download-panel">
      <div class="dp-title">Ready for {company_display}</div>
      <div class="dp-sub">
        Four persona-tailored briefing documents. Send each directly to the relevant
        stakeholder, or share the full kit with your champion to distribute internally.
      </div>
    </div>
    """)

    COLORS = {
        "cmo": ("#00C896", "CMO Brief",     "Marketing performance, ROAS, attribution"),
        "cfo": ("#E8630A", "CFO Brief",     "Financial risk, ROI, payback period"),
        "gc":  ("#D42B4A", "GC / CCO Brief","Regulatory landscape, enforcement cases"),
        "cto": ("#1A8BFF", "CTO / IT Brief","Architecture, implementation, security"),
    }

    dl_cols = st.columns(4)
    for col, (key, (color, label, desc)) in zip(dl_cols, COLORS.items()):
        with col:
            st.markdown(
                f'<div style="background:{color}18;border:1px solid {color}44;border-radius:4px;'
                f'padding:0.8rem;text-align:center;margin-bottom:0.5rem">'
                f'<div style="font-size:0.62rem;font-weight:700;letter-spacing:0.12em;'
                f'text-transform:uppercase;color:{color};margin-bottom:0.25rem">{key.upper()}</div>'
                f'<div style="font-size:0.78rem;font-weight:700;color:#E8EDF5;margin-bottom:0.2rem">{label}</div>'
                f'<div style="font-size:0.65rem;color:rgba(232,237,245,0.35);line-height:1.5">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                label=f"↓  Download",
                data=briefs[key],
                file_name=f"freshpaint_{key}_brief_{slug}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"dl_{key}",
            )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    zip_col, _ = st.columns([1, 2])
    with zip_col:
        st.download_button(
            label="↓  Download All Four (ZIP)",
            data=st.session_state["zip_bytes"],
            file_name=f"freshpaint_stakeholder_kit_{slug}.zip",
            mime="application/zip",
            use_container_width=True,
        )

    st.markdown(
        '<div style="font-size:0.65rem;color:rgba(232,237,245,0.2);margin-top:0.75rem">'
        'PDFs are generated locally and not stored. Regenerate anytime to update with new inputs.'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 1rem;margin-top:3rem;
            border-top:1px solid rgba(255,255,255,0.05);
            font-size:0.65rem;color:rgba(232,237,245,0.2);line-height:1.8">
  <a href="https://freshpaint.io" style="color:rgba(0,255,178,0.4);text-decoration:none">Freshpaint</a>
  · HIPAA-Compliant Healthcare Analytics ·
  <a href="https://freshpaint.io/blog" style="color:rgba(0,255,178,0.4);text-decoration:none">Blog</a>
  <br>Benchmarks are directional estimates based on industry data. Not legal or financial advice.
</div>
""", unsafe_allow_html=True)
