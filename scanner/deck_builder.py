"""
Stakeholder deck builder — generates persona-specific PDF briefs.
One form input produces four tailored one-pagers: CMO, CFO, GC/CCO, CTO.
"""

from fpdf import FPDF
import zipfile
import io
from datetime import date

# ── Persona configs ───────────────────────────────────────────────────────────
PERSONAS = {
    "cmo": {
        "title": "Chief Marketing Officer",
        "short": "CMO",
        "accent": (0, 200, 150),
        "focus": "Marketing Performance & Analytics",
        "headline": "Keep full marketing visibility.\nEliminate HIPAA risk.",
    },
    "cfo": {
        "title": "Chief Financial Officer",
        "short": "CFO",
        "accent": (232, 99, 10),
        "focus": "Financial Risk & ROI",
        "headline": "Quantify the liability.\nJustify the investment.",
    },
    "gc": {
        "title": "General Counsel / Chief Compliance Officer",
        "short": "GC / CCO",
        "accent": (212, 43, 74),
        "focus": "Legal & Regulatory Compliance",
        "headline": "Build a defensible\nHIPAA compliance position.",
    },
    "cto": {
        "title": "Chief Technology Officer / VP Engineering",
        "short": "CTO / IT",
        "accent": (26, 139, 255),
        "focus": "Technical Implementation & Security",
        "headline": "One integration.\nNo new infrastructure.",
    },
}

# ── Supporting data ───────────────────────────────────────────────────────────
STATE_LAWS = {
    "CA": ("CCPA / CPRA", "Sensitive data category; right to limit sharing. Health data requires opt-in."),
    "TX": ("TX THIPA", "Texas Health Information Privacy Act. Applies beyond HIPAA-covered entities."),
    "WA": ("My Health MY Data Act", "Broadest state health privacy law. Includes private right of action."),
    "VA": ("Virginia VCDPA", "Sensitive personal data restrictions apply to health information."),
    "CO": ("Colorado Privacy Act", "Sensitive data protections; opt-in consent required for health data."),
    "CT": ("Connecticut CTDPA", "Consumer data rights including health information."),
    "FL": ("Florida Digital Bill of Rights", "Applies to large data controllers processing sensitive health data."),
    "NY": ("NY SHIELD Act", "Broad security requirements; proposed Health Data Privacy Act pending."),
    "OR": ("Oregon OCPA", "Sensitive data processing restrictions; health data covered."),
    "MT": ("Montana CDPA", "Sensitive personal data protections enacted 2023."),
    "NV": ("Nevada SB 220", "Online privacy and health data provisions."),
    "IL": ("Illinois BIIPA", "Biometric focus; digital health apps should review."),
}

ORG_PROFILES = {
    "Digital Health / DTC":      {"roas_mult": 1.30, "attr_mult": 1.20},
    "Telehealth":                 {"roas_mult": 1.35, "attr_mult": 1.25},
    "Specialty Practice / Group": {"roas_mult": 1.10, "attr_mult": 1.05},
    "Hospital / Health System":   {"roas_mult": 0.90, "attr_mult": 1.10},
    "Payer / Insurance":          {"roas_mult": 1.05, "attr_mult": 1.30},
}

ENFORCEMENT_CASES = [
    ("BetterHelp",          "$7.8M",     "FTC — 2023",
     "Meta Pixel on mental health platform shared therapy session data with advertisers. "
     "FTC found this violated the Health Breach Notification Rule."),
    ("GoodRx",              "$1.5M",     "FTC — 2023",
     "Tracking pixels shared prescription drug search data with Meta, Google, and Criteo "
     "without user authorization or disclosure."),
    ("Advocate Aurora",     "$12.25M",   "Class action — 2023",
     "MyChart portal and scheduling pages ran Meta Pixel and session recording tools "
     "that captured appointment types, medical conditions, and patient identifiers."),
    ("Novant Health",       "Settlement","Class action — 2023",
     "Meta Pixel on patient scheduling portal captured appointment types and conditions. "
     "Breach notification sent to 1.3 million patients."),
    ("Cerebral",            "Class action","Private — 2023",
     "TikTok Pixel and Meta Pixel on telehealth platform exposed mental health data "
     "of 3.1 million users including diagnoses and treatment details."),
    ("BCBS Massachusetts",  "Ongoing",   "Class action — 2024",
     "Analytics and pixel tools on member portal alleged to share health data "
     "with advertisers in violation of HIPAA and Massachusetts wiretap statutes."),
]

_DARK = (11, 22, 40)
_WHITE = (255, 255, 255)
_LIGHT = (245, 247, 252)
_DIM   = (130, 148, 172)
_TEXT  = (30, 40, 58)


def _safe(text: str) -> str:
    return (
        text
        .replace("\u2014", "--").replace("\u2013", "-")
        .replace("\u2019", "'").replace("\u2018", "'")
        .replace("\u201C", '"').replace("\u201D", '"')
        .replace("\u2022", "*").replace("\u00B7", ".")
        .replace("\u2192", "->").replace("\u00AE", "(R)")
        .encode("latin-1", errors="replace").decode("latin-1")
    )


def _calc_roi(monthly_spend: float, org_type: str, freshpaint_cost: float = 40_000):
    p = ORG_PROFILES.get(org_type, ORG_PROFILES["Hospital / Health System"])
    ann = monthly_spend * 12
    roas = ann * 0.70 * 0.20 * p["roas_mult"]
    attr = ann * 0.15 * p["attr_mult"]
    rmkt = ann * 0.25 * 2.0 / 3.0
    total = roas + attr + rmkt
    return {
        "annual_spend": ann,
        "roas_loss": roas,
        "attr_loss": attr,
        "rmkt_loss": rmkt,
        "total": total,
        "roi": total / freshpaint_cost if freshpaint_cost else 0,
        "payback": freshpaint_cost / (total / 12) if total else 0,
        "freshpaint_cost": freshpaint_cost,
    }


# ── Base PDF class ─────────────────────────────────────────────────────────────
class BriefBase(FPDF):
    def __init__(self, persona_key: str, data: dict):
        super().__init__()
        self.persona  = PERSONAS[persona_key]
        self.data     = data
        self.accent   = self.persona["accent"]
        self.set_margins(18, 62, 18)
        self.set_auto_page_break(auto=True, margin=22)

    def normalize_text(self, text: str) -> str:
        return _safe(text)

    # ── Shared page furniture ──────────────────────────────────────────────
    def header(self):
        # Full-width dark band
        self.set_fill_color(*_DARK)
        self.rect(0, 0, 210, 55, "F")

        # Accent left stripe
        self.set_fill_color(*self.accent)
        self.rect(0, 0, 5, 55, "F")

        # Freshpaint wordmark
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*self.accent)
        self.set_xy(10, 8)
        self.cell(0, 5, "FRESHPAINT  |  HIPAA-COMPLIANT HEALTHCARE ANALYTICS")

        # Persona badge
        r, g, b = self.accent
        badge_text = f"  FOR THE {self.persona['short']}  "
        self.set_font("Helvetica", "B", 7)
        w = self.get_string_width(badge_text) + 2
        self.set_fill_color(r, g, b)
        self.set_text_color(*_DARK)
        self.set_xy(10, 15)
        self.cell(w, 6, badge_text, fill=True)

        # Company name
        company = _safe(self.data.get("company", "Your Organization"))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*_DIM)
        self.set_xy(10 + w + 3, 16.5)
        self.cell(0, 4, f"Prepared for {company}")

        # Headline
        lines = self.persona["headline"].split("\n")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(245, 248, 255)
        self.set_xy(10, 26)
        self.cell(0, 8, _safe(lines[0]))
        if len(lines) > 1:
            self.set_font("Helvetica", "", 14)
            self.set_text_color(*self.accent)
            self.set_xy(10, 34)
            self.cell(0, 7, _safe(lines[1]))

        # Focus label top-right
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_DIM)
        self.set_xy(0, 48)
        self.cell(200, 5, _safe(self.persona["focus"]), align="R")

    def footer(self):
        self.set_fill_color(*_DARK)
        self.rect(0, 280, 210, 17, "F")
        self.set_fill_color(*self.accent)
        self.rect(0, 280, 5, 17, "F")

        rep = _safe(self.data.get("rep_name", "Your Freshpaint Account Executive"))
        email = _safe(self.data.get("rep_email", "sales@freshpaint.io"))
        today = date.today().strftime("%B %Y")

        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*self.accent)
        self.set_xy(10, 283)
        self.cell(80, 4, rep)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_DIM)
        self.set_xy(10, 287)
        self.cell(80, 4, email)

        self.set_font("Helvetica", "", 6.5)
        self.set_text_color(*_DIM)
        self.set_xy(0, 283)
        self.cell(198, 4, f"freshpaint.io  --  {today}  --  Confidential", align="R")
        self.set_xy(0, 287)
        self.cell(198, 4, "This document contains forward-looking benchmarks. Not legal advice.", align="R")

    # ── Layout helpers ─────────────────────────────────────────────────────
    def section_head(self, title: str):
        self.ln(4)
        self.set_fill_color(*self.accent)
        self.rect(self.l_margin, self.get_y(), 3, 6, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_TEXT)
        self.set_x(self.l_margin + 5)
        self.cell(0, 6, _safe(title.upper()), ln=True)
        self.ln(1)

    def body(self, text: str, indent: int = 0):
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*_TEXT)
        self.set_x(self.l_margin + indent)
        self.multi_cell(174 - indent, 5, _safe(text))

    def bullet(self, text: str, indent: int = 4):
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*_TEXT)
        self.set_x(self.l_margin + indent)
        self.cell(5, 5, "-")
        self.set_x(self.l_margin + indent + 5)
        self.multi_cell(170 - indent, 5, _safe(text))

    def callout_row(self, items: list):
        """items = [(value, label, color_rgb), ...]"""
        col_w = 174 / len(items)
        x0 = self.l_margin
        y0 = self.get_y()
        for val, label, color in items:
            self.set_fill_color(245, 247, 252)
            self.rect(x0, y0, col_w - 2, 20, "F")
            self.set_fill_color(*color)
            self.rect(x0, y0, col_w - 2, 3, "F")
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(*color)
            self.set_xy(x0, y0 + 4)
            self.cell(col_w - 2, 8, _safe(str(val)), align="C")
            self.set_font("Helvetica", "", 6.5)
            self.set_text_color(*_DIM)
            self.set_xy(x0, y0 + 12)
            self.cell(col_w - 2, 5, _safe(label), align="C")
            x0 += col_w
        self.set_y(y0 + 24)

    def divider(self):
        self.ln(3)
        self.set_draw_color(220, 225, 235)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(4)

    def highlight_box(self, text: str, color=None):
        if color is None:
            color = self.accent
        r, g, b = color
        y = self.get_y()
        self.set_fill_color(r, g, b, )
        self.set_fill_color(int(r * 0.1 + 245 * 0.9), int(g * 0.1 + 247 * 0.9), int(b * 0.1 + 252 * 0.9))
        self.rect(self.l_margin, y, 174, 14, "F")
        self.set_fill_color(*color)
        self.rect(self.l_margin, y, 3, 14, "F")
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*_TEXT)
        self.set_xy(self.l_margin + 6, y + 4)
        self.multi_cell(165, 5, _safe(text))
        self.ln(3)

    def kv(self, key: str, value: str):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*_DIM)
        self.set_x(self.l_margin)
        self.cell(45, 5, _safe(key), ln=False)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*_TEXT)
        self.multi_cell(129, 5, _safe(value))


# ── CMO Brief ─────────────────────────────────────────────────────────────────
def _build_cmo(data: dict) -> bytes:
    m = data["metrics"]
    pdf = BriefBase("cmo", data)
    pdf.add_page()

    pdf.section_head("The Marketing Performance Risk")
    pdf.body(
        "Healthcare organizations removing tracking pixels without replacing them lose "
        "three compounding revenue streams simultaneously. Algorithmic ad optimization "
        "degrades, budget flows to the wrong channels, and remarketing audiences expire."
    )
    pdf.ln(3)
    pdf.callout_row([
        (f"${m['roas_loss']:,.0f}/yr",  "ROAS Signal Degradation",   (220, 50, 80)),
        (f"${m['attr_loss']:,.0f}/yr",  "Attribution Blindness Waste", (200, 100, 20)),
        (f"${m['rmkt_loss']:,.0f}/yr",  "Remarketing Audience Loss",  (180, 160, 20)),
    ])

    pdf.section_head("What 'Going Dark' Looks Like in Practice")
    bullets = [
        "Google Smart Bidding and Meta Advantage+ need 50+ monthly conversions to optimize. "
        "Without pixel data, they revert to broad targeting -- CAC increases 20-30%.",
        "Last-click attribution replaces multi-touch, causing over-investment in brand search "
        "and under-investment in condition-specific and awareness channels.",
        "Remarketing audiences expire within 30-90 days. Retargeting -- which typically "
        "converts 2-4x better than cold prospecting -- stops performing.",
        "Lookalike audiences built on your best-converting patients degrade without "
        "continuous pixel data to refresh the seed audience.",
        "A/B test validity requires consistent tracking. Without it, decisions on "
        "landing pages, ad creative, and messaging lose statistical reliability.",
    ]
    for b in bullets:
        pdf.bullet(b)

    pdf.add_page()

    pdf.section_head("What Freshpaint Restores")
    pdf.body(
        "Freshpaint intercepts tracking events before they reach third-party platforms, "
        "strips any Protected Health Information from the payload, then routes clean, "
        "compliant conversion data to your existing ad platforms and analytics stack. "
        "Your campaigns never lose their optimization signals."
    )
    pdf.ln(3)

    restore_items = [
        ("Google Ads / Meta",  "Conversion signals flow normally. Smart bidding keeps learning."),
        ("Attribution",        "Full multi-touch attribution maintained across all channels."),
        ("Remarketing",        "Audiences built on sanitized behavioral data. No PHI risk."),
        ("Analytics",          "GA4, Mixpanel, Amplitude receive events -- PHI stripped in transit."),
        ("EHR Attribution",    "Optional: connect appointment and revenue data for true patient CAC."),
    ]
    for tool, desc in restore_items:
        pdf.kv(tool, desc)

    pdf.divider()
    pdf.section_head("Customer Performance Benchmarks")
    pdf.callout_row([
        ("20%+",          "ROAS lift reported\nafter Freshpaint\ndeployment",       (0, 180, 135)),
        ("100%",          "Attribution\ncoverage maintained\npost-compliance fix",  (0, 180, 135)),
        ("2-4x",          "Remarketing conversion\nadvantage preserved",            (0, 180, 135)),
        ("<2 weeks",      "Typical time to\nfull deployment",                       (0, 180, 135)),
    ])

    pdf.divider()
    pdf.section_head("Recommended Next Step")
    pdf.highlight_box(
        f"Run a free PHI Risk Scan on {_safe(data.get('company', 'your website'))} to see exactly "
        "which trackers are currently creating compliance risk -- and get a prioritized "
        "remediation plan. Freshpaint replaces all of them without losing a single conversion signal.",
        color=(0, 180, 135)
    )

    return bytes(pdf.output())


# ── CFO Brief ─────────────────────────────────────────────────────────────────
def _build_cfo(data: dict) -> bytes:
    m = data["metrics"]
    fp_cost = m["freshpaint_cost"]
    pdf = BriefBase("cfo", data)
    pdf.add_page()

    pdf.section_head("The Financial Liability Exposure")
    pdf.body(
        "HIPAA violations involving impermissible disclosure of Protected Health Information "
        "carry civil monetary penalties up to $50,000 per violation per day, with annual caps "
        "of $1.9M per violation category. For healthcare organizations using non-compliant "
        "tracking technologies, each pixel on each page constitutes a separate potential violation."
    )
    pdf.ln(3)
    pdf.callout_row([
        ("$50K",       "Max OCR penalty\nper violation per day",   (200, 40, 60)),
        ("$1.9M",      "Annual cap per\nviolation category",        (200, 40, 60)),
        ("$12.25M",    "Largest class action\nsettlement to date",  (200, 40, 60)),
    ])

    pdf.section_head("Recent Enforcement & Settlements")
    for name, amount, authority, desc in ENFORCEMENT_CASES[:4]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*_TEXT)
        pdf.set_x(pdf.l_margin)
        pdf.cell(35, 5, _safe(name), ln=False)
        r, g, b = (200, 40, 60)
        pdf.set_text_color(200, 40, 60)
        pdf.cell(22, 5, _safe(amount), ln=False)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*_DIM)
        pdf.cell(35, 5, _safe(authority), ln=False)
        pdf.set_text_color(*_TEXT)
        pdf.multi_cell(82, 5, _safe(desc))

    pdf.add_page()

    pdf.section_head("The Cost of Going Dark")
    pdf.body(
        f"Based on {_safe(data.get('company', 'your organization'))}'s estimated ad spend of "
        f"${m['annual_spend']:,.0f}/year, removing non-compliant trackers without replacing them "
        "produces the following annual efficiency losses:"
    )
    pdf.ln(3)
    pdf.callout_row([
        (f"${m['roas_loss']:,.0f}",  "Lost ROAS efficiency",      (220, 90, 20)),
        (f"${m['attr_loss']:,.0f}",  "Attribution waste",         (220, 90, 20)),
        (f"${m['rmkt_loss']:,.0f}",  "Remarketing loss",          (220, 90, 20)),
        (f"${m['total']:,.0f}",      "Total annual impact",       (200, 40, 60)),
    ])

    pdf.divider()
    pdf.section_head("Investment vs. Risk-Adjusted Cost")
    payback_str = f"{m['payback']:.1f} months" if m["payback"] < 12 else f"{m['payback']/12:.1f} years"
    pdf.callout_row([
        (f"${fp_cost:,.0f}/yr",      "Freshpaint annual\ninvestment",                       (0, 180, 135)),
        (f"{m['roi']:.1f}x",         "ROI on Freshpaint\nvs. going dark cost",              (0, 180, 135)),
        (payback_str,                "Payback period",                                       (0, 180, 135)),
        (f"${m['total'] - fp_cost:,.0f}", "Net annual savings\nvs. going dark",             (0, 180, 135)),
    ])

    pdf.ln(2)
    pdf.body(
        "Note: This ROI calculation covers only efficiency losses from going dark. It does not "
        "include the cost of an OCR investigation ($500K-$2M in legal fees), a class-action "
        "settlement ($7-12M), or the reputational and brand impact of a reported breach."
    )

    pdf.divider()
    pdf.section_head("Recommended Next Step")
    pdf.highlight_box(
        "Request a customized risk assessment and pricing proposal. Freshpaint's implementation "
        "cost is a fixed annual subscription with no infrastructure overhead or per-event fees. "
        "Signed BAA included at no additional charge.",
        color=(232, 99, 10)
    )

    return bytes(pdf.output())


# ── GC / CCO Brief ─────────────────────────────────────────────────────────────
def _build_gc(data: dict) -> bytes:
    pdf = BriefBase("gc", data)
    pdf.add_page()

    pdf.section_head("The Regulatory Landscape")
    pdf.body(
        "In December 2022, the HHS Office for Civil Rights issued a bulletin explicitly "
        "naming Meta Pixel and Google Analytics as tracking technologies that may constitute "
        "impermissible disclosure of Protected Health Information under 45 CFR 164.502. "
        "In July 2023, HHS and the FTC issued joint warning letters to 130 healthcare "
        "organizations. The FTC followed with enforcement actions totaling $9.3M in penalties."
    )
    pdf.ln(3)

    reg_items = [
        ("HHS OCR Bulletin", "Dec 2022",
         "Tracking pixels on authenticated pages (patient portals, scheduling) and "
         "unauthenticated pages where health information can be inferred from URL patterns "
         "constitute PHI. Sharing with vendors without a BAA is an impermissible disclosure."),
        ("HHS/FTC Joint Letter", "Jul 2023",
         "130 healthcare organizations warned. Google, Meta, and TikTok explicitly named. "
         "FTC Act Section 5 applies to non-HIPAA covered entities. Both agencies coordinating."),
        ("FTC Health Breach Rule", "Ongoing",
         "Health apps and non-HIPAA entities face mandatory breach notification. "
         "FTC has authority to impose civil penalties for deceptive data practices."),
        ("HIPAA Breach Notification", "Ongoing",
         "Impermissible PHI disclosure to a tracking vendor triggers mandatory 60-day "
         "notification to HHS, affected individuals, and media (breaches >500 individuals)."),
    ]
    for name, date_s, desc in reg_items:
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*_TEXT)
        pdf.set_x(pdf.l_margin)
        pdf.cell(55, 5, _safe(name), ln=False)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(212, 43, 74)
        pdf.cell(22, 5, _safe(date_s), ln=False)
        pdf.set_text_color(*_TEXT)
        pdf.multi_cell(97, 5, _safe(desc))
        pdf.ln(1)

    # State laws
    states = data.get("states", [])
    applicable = [(s, STATE_LAWS[s]) for s in states if s in STATE_LAWS]
    if applicable:
        pdf.divider()
        pdf.section_head(f"Applicable State Laws ({data.get('company', 'Your Org')})")
        for abbr, (law_name, law_desc) in applicable:
            pdf.kv(f"{abbr} -- {law_name}", law_desc)

    pdf.add_page()

    pdf.section_head("Active Enforcement Cases")
    pdf.body("These settlements and investigations define the current enforcement standard.")
    pdf.ln(2)
    for name, amount, authority, desc in ENFORCEMENT_CASES:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(212, 43, 74)
        pdf.set_x(pdf.l_margin)
        pdf.cell(38, 5, _safe(name), ln=False)
        pdf.cell(22, 5, _safe(amount), ln=False)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*_DIM)
        pdf.cell(32, 5, _safe(authority), ln=False)
        pdf.set_text_color(*_TEXT)
        pdf.multi_cell(82, 5, _safe(desc))

    pdf.divider()
    pdf.section_head("Freshpaint's Defensible Compliance Position")
    defense_items = [
        ("Signed BAA",
         "Freshpaint signs a HIPAA Business Associate Agreement covering all data processed "
         "through the platform. This is a prerequisite for compliant use of any downstream tool."),
        ("PHI Sanitization",
         "All tracking events are intercepted and scrubbed of PHI before transmission "
         "to any third-party tool. No PHI transits through non-BAA-covered services."),
        ("Audit Trail",
         "Full logging of what data was collected, sanitized, and routed -- providing "
         "documentary evidence of compliance for OCR investigation defense."),
        ("OCR Guidance Alignment",
         "Freshpaint's architecture follows the approach outlined in HHS's updated "
         "guidance for compliant use of online tracking technologies in healthcare."),
        ("No Off-Ramp PHI",
         "Downstream destinations (Google Ads, Meta, analytics platforms) receive "
         "only sanitized events -- never raw PHI -- eliminating the impermissible disclosure."),
    ]
    for title, desc in defense_items:
        pdf.kv(title, desc)

    pdf.divider()
    pdf.section_head("Recommended Next Step")
    pdf.highlight_box(
        "Request Freshpaint's legal documentation package: BAA template, SOC 2 Type II report, "
        "security questionnaire responses, and a one-page technical architecture diagram "
        "suitable for inclusion in your HIPAA compliance documentation.",
        color=(212, 43, 74)
    )

    return bytes(pdf.output())


# ── CTO / IT Brief ────────────────────────────────────────────────────────────
def _build_cto(data: dict) -> bytes:
    m = data["metrics"]
    pdf = BriefBase("cto", data)
    pdf.add_page()

    pdf.section_head("How Freshpaint Works")
    pdf.body(
        "Freshpaint is a server-side event routing layer, not a replacement analytics platform. "
        "A single script tag replaces your existing tracking pixels. Events are intercepted "
        "client-side, PHI is stripped on Freshpaint's HIPAA-compliant infrastructure, "
        "and sanitized events are forwarded to your existing destinations."
    )
    pdf.ln(3)

    # ASCII-style architecture diagram
    arch_lines = [
        "  [User browser]",
        "       |",
        "       | All events intercepted",
        "       v",
        "  [Freshpaint SDK]  <-- replaces individual pixels",
        "       |",
        "       | PHI stripped, events sanitized",
        "       v",
        "  [Freshpaint HIPAA-compliant infrastructure]",
        "       |",
        "       +-----> Google Ads (conversion signals)",
        "       +-----> Meta CAPI (off-site conversions)",
        "       +-----> Google Analytics 4",
        "       +-----> Your CDP (Segment, mParticle)",
        "       +-----> EHR / scheduling system",
        "       +-----> 100+ other destinations",
    ]
    self_ref = pdf
    self_ref.set_font("Courier", "", 7.5)
    self_ref.set_fill_color(*_LIGHT)
    self_ref.rect(self_ref.l_margin, self_ref.get_y(), 174, len(arch_lines) * 4.5 + 4, "F")
    self_ref.set_text_color(26, 139, 255)
    y_start = self_ref.get_y() + 2
    for i, line in enumerate(arch_lines):
        self_ref.set_xy(self_ref.l_margin + 2, y_start + i * 4.5)
        self_ref.cell(0, 4.5, _safe(line))
    self_ref.set_y(y_start + len(arch_lines) * 4.5 + 4)

    pdf.divider()
    pdf.section_head("Implementation Overview")
    pdf.callout_row([
        ("1-3 days",   "Basic tracking\ndeployment",              (26, 139, 255)),
        ("1-2 weeks",  "Full attribution\nconfiguration",         (26, 139, 255)),
        ("0",          "New infrastructure\nto provision",        (0, 180, 135)),
        ("100+",       "Native integrations\nout of the box",     (26, 139, 255)),
    ])

    steps = [
        ("Step 1 (Day 1)",    "Replace existing pixel tags with a single Freshpaint script tag "
                              "via GTM or direct implementation. Existing analytics continue running."),
        ("Step 2 (Day 1-2)",  "Configure PHI allowlists: define which event properties are safe "
                              "to route downstream. Freshpaint blocks everything else by default."),
        ("Step 3 (Week 1)",   "Connect destinations: point Freshpaint to your existing Google Ads, "
                              "Meta, analytics, and CDP accounts using API credentials."),
        ("Step 4 (Week 2)",   "Optional: connect EHR/scheduling system for closed-loop attribution "
                              "(appointment booked -> attended -> revenue)."),
    ]
    for step, desc in steps:
        pdf.kv(step, desc)

    pdf.add_page()

    pdf.section_head("Security & Compliance Posture")
    security_items = [
        ("SOC 2 Type II",       "Annual third-party audit of security controls, availability, "
                                "and confidentiality. Report available under NDA."),
        ("HIPAA BAA",           "Standard BAA executed at contract signature. Covers all data "
                                "processed through the Freshpaint platform."),
        ("Data Residency",      "All PHI-containing events processed on US-based infrastructure. "
                                "No data transferred to non-US servers."),
        ("Encryption",          "TLS 1.2+ in transit. AES-256 at rest. Keys managed per customer."),
        ("Access Controls",     "Role-based access, SSO/SAML support, MFA required. "
                                "Full audit log of admin and configuration changes."),
        ("Penetration Testing", "Annual third-party pen test. Results available under NDA."),
        ("Vendor Risk",         "No subprocessors with access to raw PHI. "
                                "Freshpaint's subprocessor list available in BAA exhibit."),
        ("PHI Retention",       "Configurable. Default: PHI stripped before routing; "
                                "sanitized events retained per customer data retention policy."),
    ]
    for item, desc in security_items:
        pdf.kv(item, desc)

    pdf.divider()
    pdf.section_head("Integration Compatibility")
    pdf.body(
        "Freshpaint works alongside your existing stack -- it does not replace any tool. "
        "Current integrations include:"
    )
    pdf.ln(2)
    categories = [
        ("Ad Platforms",     "Google Ads, Meta CAPI, LinkedIn, TikTok, Microsoft Ads, Programmatic"),
        ("Analytics",        "Google Analytics 4, Adobe Analytics, Mixpanel, Amplitude, Heap"),
        ("CDPs",             "Segment, mParticle, Tealium, Rudderstack"),
        ("CRM / Marketing",  "Salesforce, HubSpot, Marketo, Pardot"),
        ("EHR / Clinical",   "Epic (FHIR R4), athenahealth, Cerner, eClinicalWorks"),
        ("Data Warehouse",   "Snowflake, BigQuery, Redshift, Databricks"),
    ]
    for cat, tools in categories:
        pdf.kv(cat, tools)

    pdf.divider()
    pdf.section_head("Recommended Next Step")
    pdf.highlight_box(
        "Request a technical architecture review call. Freshpaint's implementation team will "
        "map your current tag configuration, identify PHI exposure points, and produce a "
        "deployment plan specific to your stack -- typically deliverable within 5 business days.",
        color=(26, 139, 255)
    )

    return bytes(pdf.output())


# ── Public API ────────────────────────────────────────────────────────────────
def generate_brief(persona_key: str, data: dict) -> bytes:
    data = dict(data)
    if "metrics" not in data:
        data["metrics"] = _calc_roi(
            data.get("monthly_spend", 50_000),
            data.get("org_type", "Hospital / Health System"),
            data.get("freshpaint_cost", 40_000),
        )
    builders = {"cmo": _build_cmo, "cfo": _build_cfo, "gc": _build_gc, "cto": _build_cto}
    return builders[persona_key](data)


def generate_all_zip(data: dict) -> bytes:
    data = dict(data)
    if "metrics" not in data:
        data["metrics"] = _calc_roi(
            data.get("monthly_spend", 50_000),
            data.get("org_type", "Hospital / Health System"),
            data.get("freshpaint_cost", 40_000),
        )
    slug = data.get("company", "prospect").lower().replace(" ", "_").replace(",", "")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for key in ("cmo", "cfo", "gc", "cto"):
            pdf_bytes = generate_brief(key, data)
            zf.writestr(f"freshpaint_{key}_brief_{slug}.pdf", pdf_bytes)
    buf.seek(0)
    return buf.read()
