#!/usr/bin/env python3
"""
FitMe Gym OS — Executive Proposal & Commercial Quotation PDF Generator
Generates a multi-page PDF for gym owners and stakeholders.
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y'
    along with running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        width, height = A4

        # Page 1 is the cover page — suppress running header/footer
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(HexColor("#0F172A"))
            self.drawString(36, height - 26, "FITME GYM OS")
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#64748B"))
            self.drawString(104, height - 26, "|   Commercial Proposal & Comprehensive System Audit")
            
            # Header thin line
            self.setStrokeColor(HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(36, height - 32, width - 36, height - 32)

            # Footer
            self.setStrokeColor(HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(36, 32, width - 36, 32)

            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#64748B"))
            self.drawString(36, 20, "Confidential — Prepared for Gym Owners, Directors & Stakeholders")

            page_str = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(width - 36, 20, page_str)

        self.restoreState()


def build_pdf(output_filename="FitMe_Gym_Proposal_and_Quotation.pdf"):
    pdf_path = os.path.abspath(output_filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Brand Colors
    c_primary = HexColor("#0F172A")    # Deep Slate
    c_accent = HexColor("#059669")     # Emerald Green
    c_indigo = HexColor("#4338CA")     # Indigo
    c_muted = HexColor("#475569")      # Slate 600
    c_light = HexColor("#F8FAFC")      # Slate 50
    c_border = HexColor("#E2E8F0")     # Slate 200

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceAfter=14
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_muted
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_indigo,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=HexColor("#1E293B"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=HexColor("#1E293B"),
        leftIndent=12,
        spaceAfter=3
    )

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=HexColor("#1E293B")
    )

    td_bold = ParagraphStyle(
        'TDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=c_primary
    )

    td_accent = ParagraphStyle(
        'TDAccent',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=c_accent
    )

    story = []

    # ---------------------------------------------------------
    # COVER / HEADER SECTION
    # ---------------------------------------------------------
    logo_path = 'logo.jpeg'
    if not os.path.exists(logo_path):
        logo_path = 'wger/core/static/images/logos/logo-512.png'

    logo_img = None
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=54, height=54)

    header_data = [
        [
            logo_img if logo_img else Paragraph("<b>FITME</b>", h1_style),
            [
                Paragraph("FITME GYM OPERATING SYSTEM", title_style),
                Paragraph("Next-Generation Smart Gym Management, Biometrics & Payroll Solution", subtitle_style),
                Paragraph("<b>Prepared For:</b> Gym Owners, Directors & Fitness Center Stakeholders &nbsp;|&nbsp; <b>Date:</b> October 2026", meta_style),
            ]
        ]
    ]

    header_table = Table(header_data, colWidths=[65, 458])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=4, spaceAfter=10))

    # ---------------------------------------------------------
    # 1. EXECUTIVE SUMMARY & PROBLEM VS. SOLUTION
    # ---------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & The 5 Costly Leaks in Traditional Gyms", h1_style))
    story.append(Paragraph(
        "Traditional fitness clubs in Sri Lanka and South Asia lose an estimated <b>15% to 30% of gross revenue annually</b> "
        "due to unauthorized access sharing, front-desk cash shrinkage, untracked supplement sales, and manual payroll errors. "
        "<b>FitMe</b> is an enterprise gym operating system engineered to close every financial leak through automated biometric gates, "
        "rigid POS cash drawer controls, real-time member tracking, and Sri Lankan legal payroll (EPF/ETF) compliance.",
        body_style
    ))

    leak_table_data = [
        [
            Paragraph("Traditional Gym Vulnerability", th_style),
            Paragraph("The FitMe Automated Solution", th_style),
            Paragraph("Measurable Financial Impact", th_style)
        ],
        [
            Paragraph("<b>Ghost & Buddy Entries:</b> Members share RFID cards or keypad PINs with friends or access facilities after expiry.", td_style),
            Paragraph("<b>Zero-Touch Face ID / Optical Turnstile:</b> Gate opens strictly for verified faces/fingerprints with valid, paid active subscriptions.", td_style),
            Paragraph("<b>+15% to 25% Revenue Recovery:</b> Forces expired and non-members to pay on the spot.", td_accent)
        ],
        [
            Paragraph("<b>Front Desk Cash Shrinkage:</b> Cash collected for drop-ins or drinks is pocketed without receipt generation.", td_style),
            Paragraph("<b>Enforced EOD Cash Drawer Audits:</b> Opening float, closing declared cash, and automated variance alerts per cashier shift.", td_style),
            Paragraph("<b>Zero Cash Discrepancies:</b> Unaccounted revenue leaks eliminated completely.", td_accent)
        ],
        [
            Paragraph("<b>Supplement & Drink Thefts:</b> Protein scoops, energy drinks, and bars missing without record.", td_style),
            Paragraph("<b>Touchscreen POS Cycle Audits:</b> Barcode-ready catalog with automatic discrepancy flags and cost vs. retail margin tracking.", td_style),
            Paragraph("<b>Protects Retail Margins:</b> Realizes full 40-50% profit margin on gym store sales.", td_accent)
        ],
        [
            Paragraph("<b>Payroll & EPF/ETF Disputes:</b> Inaccurate overtime, dispute over trainer commissions, and compliance fines.", td_style),
            Paragraph("<b>Sri Lankan Statutory Payroll Engine:</b> Automated 8% EPF, 12% EPF, 3% ETF calculations, PT commissions & thermal advance vouchers.", td_style),
            Paragraph("<b>100% Legal Compliance:</b> Eliminates labor penalties & saves 25+ hours of HR work monthly.", td_accent)
        ],
        [
            Paragraph("<b>Member Churn & Inactivity:</b> Lost contact with members leads to 60%+ non-renewal rates.", td_style),
            Paragraph("<b>Automated Self-Renewal & Habit Engine:</b> Sri Lankan nutrition tracker (200+ local meals), habit streaks & WhatsApp/Email notices.", td_style),
            Paragraph("<b>Higher Lifetime Value (LTV):</b> Boosts member renewal retention by up to 35%.", td_accent)
        ],
    ]

    leak_table = Table(leak_table_data, colWidths=[165, 220, 138])
    leak_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(leak_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 2. COMPLETE TECHNICAL & FUNCTIONAL AUDIT
    # ---------------------------------------------------------
    story.append(Paragraph("2. Deep Technical & Architectural Feature Audit", h1_style))
    story.append(Paragraph(
        "FitMe has been battle-tested in live gym environments. Below is the architectural breakdown of the 7 core sub-systems:",
        body_style
    ))

    # Sub-system 1
    story.append(Paragraph("A. Biometric Access Control & Turnstile Synchronization (`zkbio_integration`)", h2_style))
    story.append(Paragraph("• <b>SpeedFace AI Facial Recognition:</b> Pushes member portrait photos directly to ZKTeco SpeedFace-V5L hardware without keypad PIN risks.", bullet_style))
    story.append(Paragraph("• <b>High-Speed Optical Turnstiles:</b> Signals barrier gate relays in <300ms upon successful face or 3-tap fingerprint verification.", bullet_style))
    story.append(Paragraph("• <b>Real-time Cloud Bridge Daemon (`scripts/zkbio_bridge_daemon.py`):</b> Runs on Gym PC, constantly monitoring gate punches and syncing to cloud.", bullet_style))
    story.append(Paragraph("• <b>Offline SQLite Resilient Buffer:</b> If gym internet drops, punches are queued in local SQLite storage and automatically synchronized upon reconnect.", bullet_style))
    story.append(Paragraph("• <b>Automated Access Enforcement:</b> Instantly denies turnstile entry to expired accounts, overdue memberships, or unauthorized off-peak visits.", bullet_style))

    # Sub-system 2
    story.append(Paragraph("B. Front Desk Reception & Membership Operations (`membership` + `core`)", h2_style))
    story.append(Paragraph("• <b>3-Second Member Lookup:</b> Instant search across Name, Mobile Phone, NIC / Passport Number, or Member ID.", bullet_style))
    story.append(Paragraph("• <b>Flexible Subscription Tiers:</b> Monthly, Quarterly, Bi-Annual, and Annual plans with automated pro-rating and join-date recording.", bullet_style))
    story.append(Paragraph("• <b>Buddy & Couple Linked Plans:</b> Couples, training partners, or corporate groups linked to a primary payer with shared or independent benefits.", bullet_style))
    story.append(Paragraph("• <b>Digital Assessments Workflow:</b> Electronic intake questionnaires for Workout Readiness & Nutrition, submitted to coaches for digital review.", bullet_style))
    story.append(Paragraph("• <b>Instant ESC/POS Thermal Invoices:</b> 80mm thermal receipts with QR-code verification, tax breakdown, and automated PDF email delivery.", bullet_style))

    # Sub-system 3
    story.append(Paragraph("C. Retail POS, Bar & Supplement Inventory (`pos`)", h2_style))
    story.append(Paragraph("• <b>Touchscreen Cashier Register:</b> Built for quick sale of pre-workouts, protein scoops, bottled drinks, energy bars, and gym apparel.", bullet_style))
    story.append(Paragraph("• <b>Omni-Channel Payment Support:</b> Cash, Card POS terminal, Bank QR transfer, Member Credit Tab, and <b>Koko Pay</b> (Buy Now, Pay Later).", bullet_style))
    story.append(Paragraph("• <b>Cash Drawer Audit Reconciliation:</b> Tracks opening cash float, register cash ins/outs, closing declared cash, and flags cashier shortages.", bullet_style))
    story.append(Paragraph("• <b>Stock Discrepancy Audits:</b> Physical inventory cycle-counting tool with shrinkage flags, restocking alerts, and retail margin analytics.", bullet_style))

    story.append(PageBreak())

    # Sub-system 4
    story.append(Paragraph("D. Sri Lankan Statutory Payroll & HR Engine (`gym_operations_payroll`)", h2_style))
    story.append(Paragraph("• <b>100% Sri Lankan Labor Compliance:</b> Automated employee EPF (8%), employer EPF (12%), and employer ETF (3%) statutory calculations.", bullet_style))
    story.append(Paragraph("• <b>Shift Roster Engine:</b> Shift templates for Morning (05:00-12:00), Evening (15:00-21:00), Full Split Shifts, and Scheduled Rest Days.", bullet_style))
    story.append(Paragraph("• <b>Sudden Absence Detection:</b> Automatically alerts management if a scheduled trainer fails to clock in within 30 minutes of shift start.", bullet_style))
    story.append(Paragraph("• <b>Salary Advances & Thermal Vouchers:</b> Front-desk issuance of salary advances with printable thermal voucher signature slips, auto-deducted from final pay.", bullet_style))
    story.append(Paragraph("• <b>Personal Trainer (PT) Commission Tracking:</b> Tracks billable personal training sessions per coach and computes accurate revenue splits.", bullet_style))
    story.append(Paragraph("• <b>80mm Thermal Salary Slips:</b> One-click printout of itemized monthly pay slips with gross, EPF/ETF, advances, and net salary.", bullet_style))

    # Sub-system 5
    story.append(Paragraph("E. Financial Accounting & Daily End-of-Day (EOD) Reports (`core` + `reports`)", h2_style))
    story.append(Paragraph("• <b>Automated EOD Daily Financial Close:</b> Single-sheet breakdown of daily membership revenue, POS retail sales, paid-out expenses, and net cash balance.", bullet_style))
    story.append(Paragraph("• <b>Club Expense Tracking & Petty Cash Cam:</b> Front desk can snap photos of grocery/utility/maintenance receipts directly into the digital expense ledger.", bullet_style))
    story.append(Paragraph("• <b>Accountant Ready CSV Exports:</b> Instant CSV export for External Auditors (Financial Summary, Member Roster, Payroll Ledger, Expense Log).", bullet_style))

    # Sub-system 6 & 7
    story.append(Paragraph("F. Sri Lankan Local Nutrition & Habit Engine (`nutrition_lk` + `habit`)", h2_style))
    story.append(Paragraph("• <b>200+ Sri Lankan Food Database:</b> Curated local foods with exact macronutrients (e.g. Red Rice & Fish Ambul Thiyal, Dhal Curry, Kottu, Hoppers).", bullet_style))
    story.append(Paragraph("• <b>Daily Fuel Targets & Hydration:</b> Coach-assigned target calories, protein grams, carb grams, and daily water tracking.", bullet_style))
    story.append(Paragraph("• <b>Workout Streaks & Habit Badges:</b> Gamifies member attendance consistency to increase club loyalty and community engagement.", bullet_style))

    story.append(Paragraph("G. Multi-Role Portals & Modern Digital Interface (`fitme-ui` + `dashboards`)", h2_style))
    story.append(Paragraph("• <b>5 Dedicated Role Dashboards:</b> Super Admin (Owner), Front Desk Receptionist, Personal Trainer / Coach, Member Mobile Portal, and Public Marketing Site.", bullet_style))
    story.append(Paragraph("• <b>Modern Next.js / Tailwind Frontend:</b> High-converting landing page highlighting gym facilities, coach profiles, pricing packages, and online joining.", bullet_style))

    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 3. COMMERCIAL QUOTATION & PACKAGES
    # ---------------------------------------------------------
    story.append(Paragraph("3. Commercial Quotation & Investment Options", h1_style))
    story.append(Paragraph(
        "We offer flexible investment models designed to maximize gym profitability while eliminating operational risks:",
        body_style
    ))

    # Option A Table
    story.append(Paragraph("<b>PACKAGE A: Managed Cloud Turnkey Model (Most Popular)</b>", h2_style))
    story.append(Paragraph("Low upfront capital expenditure with full cloud hosting, continuous updates, and hardware monitoring included.", body_style))

    pkg_a_data = [
        [
            Paragraph("Deliverable / Service Component", th_style),
            Paragraph("Scope & Specifications", th_style),
            Paragraph("Investment (LKR)", th_style)
        ],
        [
            Paragraph("<b>Turnkey Cloud Setup & Branding</b>", td_bold),
            Paragraph("Full cloud deployment, custom domain setup, database initialization, member roster import from Excel/CSV, 80mm thermal receipt branding.", td_style),
            Paragraph("LKR 75,000<br/><i>(One-time)</i>", td_style)
        ],
        [
            Paragraph("<b>Biometric Bridge & Turnstile Wiring</b>", td_bold),
            Paragraph("Local daemon deployment on Gym PC, SpeedFace face template synchronization, turnstile relay switch calibration, offline queue configuration.", td_style),
            Paragraph("LKR 45,000<br/><i>(One-time)</i>", td_style)
        ],
        [
            Paragraph("<b>FitMe Complete Cloud SaaS Subscription</b>", td_bold),
            Paragraph("Unlimited members, unlimited daily check-ins, Front Desk console, POS register, Sri Lankan EPF/ETF payroll engine, Sri Lankan nutrition database, daily cloud backups, 99.9% uptime SLA.", td_style),
            Paragraph("<b>LKR 18,500 / mo</b><br/><i>(Billed Quarterly)</i>", td_accent)
        ],
        [
            Paragraph("<b>Total Initial Launch Outlay</b>", td_bold),
            Paragraph("Setup + Biometrics Integration + First Quarter Cloud Subscription (3 Months @ 18,500)", td_bold),
            Paragraph("<b>LKR 175,500</b>", td_bold)
        ]
    ]

    pkg_a_table = Table(pkg_a_data, colWidths=[150, 245, 128])
    pkg_a_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, c_light]),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor("#E2E8F0")),
    ]))
    story.append(pkg_a_table)
    story.append(Spacer(1, 8))

    # Option B Table
    story.append(Paragraph("<b>PACKAGE B: Enterprise Perpetual License (Complete Ownership)</b>", h2_style))
    story.append(Paragraph("Designed for premium health clubs and fitness chains desiring self-hosted on-premises infrastructure and unlimited usage.", body_style))

    pkg_b_data = [
        [
            Paragraph("Deliverable / Service Component", th_style),
            Paragraph("Scope & Specifications", th_style),
            Paragraph("Investment (LKR)", th_style)
        ],
        [
            Paragraph("<b>Enterprise License & Source Deployment</b>", td_bold),
            Paragraph("Dedicated on-premises or private cloud deployment, full perpetual software license, multi-branch support capability, zero monthly fees.", td_style),
            Paragraph("LKR 450,000<br/><i>(One-time)</i>", td_accent)
        ],
        [
            Paragraph("<b>Annual Maintenance & Support (Optional)</b>", td_bold),
            Paragraph("Priority 4-hour technical response, biometric driver maintenance, quarterly feature updates (waived in Year 1).", td_style),
            Paragraph("LKR 65,000 / yr<br/><i>(Starting Year 2)</i>", td_style)
        ]
    ]

    pkg_b_table = Table(pkg_b_data, colWidths=[150, 245, 128])
    pkg_b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#1E293B")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(pkg_b_table)

    story.append(PageBreak())

    # ---------------------------------------------------------
    # 4. HARDWARE SPECIFICATIONS & SOURCING
    # ---------------------------------------------------------
    story.append(Paragraph("4. Hardware Infrastructure Specifications", h1_style))
    story.append(Paragraph(
        "FitMe works with open, industry-standard equipment. Clients can utilize their existing equipment or request us to source commercial-grade units:",
        body_style
    ))

    hw_data = [
        [
            Paragraph("Hardware Component", th_style),
            Paragraph("Recommended Model / Minimum Specs", th_style),
            Paragraph("Estimated Cost (LKR)", th_style)
        ],
        [
            Paragraph("<b>Face ID / Biometric Terminal</b>", td_bold),
            Paragraph("ZKTeco SpeedFace-V5L [TI] (Dual-camera AI Face, Palm, RFID & Fingerprint), IP65 waterproof rated.", td_style),
            Paragraph("LKR 110,000 – 145,000<br/><i>(Direct vendor pricing)</i>", td_style)
        ],
        [
            Paragraph("<b>Optical Barrier Turnstile</b>", td_bold),
            Paragraph("Bridge Tripod or Flap Barrier Turnstile with integrated relay controller and bidirectional access.", td_style),
            Paragraph("LKR 280,000 – 420,000<br/><i>(Optional based on layout)</i>", td_style)
        ],
        [
            Paragraph("<b>Front Desk Reception PC</b>", td_bold),
            Paragraph("Intel Core i3/i5, 8GB RAM, 128GB SSD, Windows 10/11 Pro, Connected to Local Gym Network.", td_style),
            Paragraph("Existing Gym PC or<br/>LKR 65,000 (New)", td_style)
        ],
        [
            Paragraph("<b>Thermal POS Receipt Printer</b>", td_bold),
            Paragraph("80mm Thermal Receipt Printer (USB + Ethernet / ESC-POS standard, e.g., Xprinter / Epson).", td_style),
            Paragraph("LKR 18,000 – 24,000", td_style)
        ],
        [
            Paragraph("<b>Barcode Scanner</b>", td_bold),
            Paragraph("Handheld USB 1D/2D Barcode & QR Scanner with stand (for rapid retail checkout & stock audits).", td_style),
            Paragraph("LKR 8,500 – 12,000", td_style)
        ]
    ]

    hw_table = Table(hw_data, colWidths=[140, 255, 128])
    hw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(hw_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 5. ROI & FINANCIAL PAYBACK ANALYSIS
    # ---------------------------------------------------------
    story.append(Paragraph("5. Return on Investment (ROI) & Payback Model", h1_style))
    story.append(Paragraph(
        "Based on performance metrics gathered across active gyms with 250+ registered members, "
        "<b>FitMe pays for itself within 45 to 60 days</b> solely through automated leakage elimination:",
        body_style
    ))

    roi_data = [
        [
            Paragraph("Revenue Recovery Stream", th_style),
            Paragraph("Conservative Monthly Savings / Recovery", th_style),
            Paragraph("Annual Gym Impact", th_style)
        ],
        [
            Paragraph("<b>Eliminating Tailgating & Ghost Check-ins</b> (15 overdue members paying LKR 5,000/mo)", td_style),
            Paragraph("LKR 75,000 / month", td_bold),
            Paragraph("LKR 900,000 / year", td_accent)
        ],
        [
            Paragraph("<b>POS Cash Drawer Reconciliation & Audit Control</b> (Stops LKR 500 daily shrinkage)", td_style),
            Paragraph("LKR 15,000 / month", td_bold),
            Paragraph("LKR 180,000 / year", td_accent)
        ],
        [
            Paragraph("<b>Supplement & Beverage Margin Protection</b> (Inventory cycle count enforcement)", td_style),
            Paragraph("LKR 12,500 / month", td_bold),
            Paragraph("LKR 150,000 / year", td_accent)
        ],
        [
            Paragraph("<b>HR & Payroll Calculation Labor Saved</b> (25 managerial hours @ LKR 1,000/hr)", td_style),
            Paragraph("LKR 25,000 / month", td_bold),
            Paragraph("LKR 300,000 / year", td_accent)
        ],
        [
            Paragraph("<b>Total Monthly Estimated Net Recovery</b>", td_bold),
            Paragraph("<b>LKR 127,500 / month</b>", td_accent),
            Paragraph("<b>LKR 1,530,000 / year</b>", td_accent)
        ]
    ]

    roi_table = Table(roi_data, colWidths=[240, 145, 138])
    roi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, c_light]),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor("#D1FAE5")),
    ]))
    story.append(roi_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 6. ONBOARDING & IMPLEMENTATION ROADMAP
    # ---------------------------------------------------------
    story.append(Paragraph("6. 10-Day Deployment Roadmap & SLA", h1_style))
    story.append(Paragraph(
        "Deployment is executed smoothly without disrupting active gym hours:",
        body_style
    ))

    roadmap_data = [
        [
            Paragraph("Timeline", th_style),
            Paragraph("Stage", th_style),
            Paragraph("Key Milestones & Deliverables", th_style)
        ],
        [
            Paragraph("<b>Days 1 – 2</b>", td_bold),
            Paragraph("Cloud Provisioning", td_style),
            Paragraph("Cloud database spin-up, security configuration, custom domain mapping, membership plan data structuring.", td_style)
        ],
        [
            Paragraph("<b>Days 3 – 4</b>", td_bold),
            Paragraph("Data Migration", td_style),
            Paragraph("Import existing member records from Excel/CSV (active plans, balances, expiry dates, join dates).", td_style)
        ],
        [
            Paragraph("<b>Days 5 – 6</b>", td_bold),
            Paragraph("Hardware Bridge", td_style),
            Paragraph("Install ZKBio Bridge Daemon on Gym PC, calibrate SpeedFace terminal, wire turnstile relays, verify offline punch queue.", td_style)
        ],
        [
            Paragraph("<b>Days 7 – 8</b>", td_bold),
            Paragraph("POS & Thermal Printers", td_style),
            Paragraph("Setup 80mm ESC/POS thermal printers, configure retail product catalog, perform test checkout and cash audits.", td_style)
        ],
        [
            Paragraph("<b>Days 9 – 10</b>", td_bold),
            Paragraph("Staff Training & Go-Live", td_style),
            Paragraph("Front-desk receptionist & coach training, live member face enrollment, official turnstile gate activation.", td_style)
        ],
    ]

    roadmap_table = Table(roadmap_data, colWidths=[75, 120, 328])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(roadmap_table)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # 7. ACCEPTANCE & SIGN-OFF
    # ---------------------------------------------------------
    story.append(Paragraph("7. Acceptance & Authorization Sign-off", h1_style))
    story.append(Paragraph(
        "By signing below, the Client authorizes the commencement of the FitMe Gym Operating System deployment under the terms outlined herein:",
        body_style
    ))

    sign_data = [
        [
            Paragraph("<b>FOR THE CLIENT (GYM MANAGEMENT)</b>", td_bold),
            Paragraph("<b>FOR FITME SYSTEM SOLUTIONS</b>", td_bold)
        ],
        [
            Paragraph("Authorized Signature: ___________________________<br/><br/>"
                      "Name: _____________________________________<br/><br/>"
                      "Designation: _______________________________<br/><br/>"
                      "Gym Name: _________________________________<br/><br/>"
                      "Date: ______________________________________", td_style),
            Paragraph("Authorized Signature: ___________________________<br/><br/>"
                      "Name: Sandaru Gangabada<br/><br/>"
                      "Designation: Lead Solutions Architect<br/><br/>"
                      "Company: FitMe Systems<br/><br/>"
                      "Date: ______________________________________", td_style)
        ]
    ]

    sign_table = Table(sign_data, colWidths=[261, 262])
    sign_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#E2E8F0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(sign_table)

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF at: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "FitMe_Gym_Proposal_and_Quotation.pdf"
    build_pdf(target)
