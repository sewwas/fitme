#!/usr/bin/env python3
"""
FitMe Gym OS — Commercial Proposal, Owner Feature Showcase & Investment Quotation
A high-converting, business-focused executive proposal tailored specifically for gym owners and stakeholders.
"""

import os
import sys

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
    along with running headers and footers tailored for gym owners.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        print(f"Generated Owner Proposal PDF with {num_pages} pages.")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        width, height = A4

        # Page 1 is the executive cover — suppress running top header
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(HexColor("#0F172A"))
            self.drawString(36, height - 24, "FITME GYM OPERATING SYSTEM")
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#64748B"))
            self.drawString(185, height - 24, "|   Software-Only Lifetime Commercial Proposal for Gym Owners (Zero Monthly Fees)")
            
            self.setStrokeColor(HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(36, height - 28, width - 36, height - 28)

        # Running Footer across all pages
        self.setStrokeColor(HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(36, 28, width - 36, 28)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(HexColor("#64748B"))
        self.drawString(36, 17, "Confidential — Prepared Exclusively for Gym Owners, Managing Directors & Fitness Entrepreneurs")

        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(width - 36, 17, page_str)

        self.restoreState()


def build_pdf(output_filename="FitMe_Gym_Proposal_and_Quotation.pdf"):
    pdf_path = os.path.abspath(output_filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Premium Brand Palette
    c_primary = HexColor("#0F172A")    # Deep Slate / Midnight Blue
    c_accent = HexColor("#059669")     # Vibrant Emerald Green (Growth & Profits)
    c_indigo = HexColor("#3730A3")     # Royal Indigo
    c_muted = HexColor("#475569")      # Slate 600
    c_light = HexColor("#F8FAFC")      # Slate 50
    c_border = HexColor("#CBD5E1")     # Slate 300
    c_tag_bg = HexColor("#ECFDF5")     # Soft Mint Green
    c_highlight = HexColor("#FEF3C7")  # Amber Highlight

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_accent,
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=c_muted
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15.5,
        textColor=c_primary,
        spaceBefore=9,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_indigo,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=HexColor("#1E293B"),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.2,
        textColor=HexColor("#1E293B"),
        leftIndent=10,
        spaceAfter=2.5
    )

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10,
        textColor=colors.white
    )

    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=HexColor("#1E293B")
    )

    td_bold = ParagraphStyle(
        'TDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=c_primary
    )

    td_accent = ParagraphStyle(
        'TDAccent',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=c_accent
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=HexColor("#065F46"),
        alignment=1  # Center
    )

    story = []

    # =========================================================
    # PAGE 1: EXECUTIVE PITCH & THE 5 HIDDEN REVENUE LEAKS
    # =========================================================
    logo_path = 'logo.jpeg'
    if not os.path.exists(logo_path):
        logo_path = 'wger/core/static/images/logos/logo-512.png'

    logo_img = None
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=66, height=44)

    header_data = [
        [
            logo_img if logo_img else Paragraph("<b>FITME</b>", h1_style),
            [
                Paragraph("FITME GYM OPERATING SYSTEM", title_style),
                Paragraph("Software-Only Lifetime License • Zero Monthly Subscription Fees • Zero Hardware Required", subtitle_style),
                Paragraph("<b>Document Ref:</b> FITME-PROP-2026-SW &nbsp;|&nbsp; <b>Release:</b> Software Lifetime Edition<br/>"
                          "<b>Target Audience:</b> Gym Owners, Managing Directors, Club Operations Heads & Fitness Center Stakeholders", meta_style),
            ]
        ]
    ]

    header_table = Table(header_data, colWidths=[75, 448])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=3, spaceAfter=5))

    # Owner Value Badges
    badge_data = [
        [
            Paragraph("🛡️ <b>Automated Turnstile Security<br/>(Stops Unpaid Walk-ins)</b>", badge_style),
            Paragraph("🇱🇰 <b>100% Sri Lankan Payroll<br/>(EPF 8%/12% & ETF 3% Legal)</b>", badge_style),
            Paragraph("🥗 <b>200+ Sri Lankan Diet Engine<br/>(Kottu, Red Rice, Ambul Thiyal)</b>", badge_style),
            Paragraph("📱 <b>Owner Phone Dashboard<br/>(Live Revenue & Attendance)</b>", badge_style),
        ]
    ]
    badge_table = Table(badge_data, colWidths=[130, 131, 131, 131])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_tag_bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#A7F3D0")),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 5))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Pitch: Why Successful Gym Owners Switch to FitMe", h1_style))
    story.append(Paragraph(
        "Running a profitable fitness club in Sri Lanka requires more than great workout equipment — it demands complete operational control. "
        "Traditional gyms unknowingly bleed <b>15% to 30% of their gross annual revenue</b> through unauthorized buddy check-ins, "
        "front-desk cash shrinkage, untracked energy drink/supplement sales, and time-consuming manual payroll errors. "
        "<b>FitMe Gym OS</b> is an enterprise gym management solution designed from the ground up for Sri Lankan fitness clubs. "
        "It eliminates cash theft, locks out unpaid visitors with AI face recognition turnstiles, automates legal EPF/ETF payroll, "
        "and keeps members renewing month after month with localized Sri Lankan nutrition and habit coaching.",
        body_style
    ))

    leak_table_data = [
        [
            Paragraph("Traditional Gym Headache", th_style),
            Paragraph("How FitMe Protects Your Business", th_style),
            Paragraph("Measurable Financial Win", th_style)
        ],
        [
            Paragraph("<b>Ghost Entries & Card Sharing:</b> Members pass RFID cards or keypad PINs to friends or work out months after subscription expiry.", td_style),
            Paragraph("<b>AI Face ID Optical Turnstiles:</b> Gate unlocks in <b><0.3 seconds</b> strictly for active, verified faces. Expired members are stopped at the door with a buzzer alert.", td_style),
            Paragraph("<b>+15% to 25% Revenue Recovery:</b> Unpaid visitors are forced to pay or renew on the spot.", td_accent)
        ],
        [
            Paragraph("<b>Front Desk Cash Discrepancies:</b> Cash collected for walk-in day passes or drop-in drinks is pocketed without receipts being generated.", td_style),
            Paragraph("<b>Dual Shift Cash Drawer Audits:</b> System enforces opening cash floats, real-time register balance tracking, and closing declared cash variance reports.", td_style),
            Paragraph("<b>Zero Cash Shrinkage:</b> Complete cash accountability for every cashier shift.", td_accent)
        ],
        [
            Paragraph("<b>Supplement & Beverage Pilferage:</b> Protein scoops, pre-workout drinks, and water bottles go missing from the reception counter untracked.", td_style),
            Paragraph("<b>Touchscreen POS & Inventory Audits:</b> Barcode-integrated checkout, automatic low-stock warnings, physical inventory cycle counts & profit margin tracking.", td_style),
            Paragraph("<b>Protects 40%–50% Profit Margins:</b> Realizes full profit potential from your gym store.", td_accent)
        ],
        [
            Paragraph("<b>Payroll Disputes & EPF/ETF Labor Fines:</b> Inaccurate trainer session records, forgotten salary advances, and statutory penalties from the Labor Dept.", td_style),
            Paragraph("<b>Automated Sri Lankan Legal Payroll:</b> Exact 8% EPF, 12% EPF, 3% ETF calculations, sudden absence alerts & 80mm thermal salary advance signature vouchers.", td_style),
            Paragraph("<b>100% Legal Compliance:</b> Eliminates labor penalties & saves 25+ hours of owner time monthly.", td_accent)
        ],
        [
            Paragraph("<b>High Member Churn (60%+ Quit):</b> Members stop coming because they lack guidance, motivation, and practical local dietary advice.", td_style),
            Paragraph("<b>Sri Lankan Nutrition & Habit Streaks:</b> 200+ local meals (Red rice, fish curry, kottu), visual water counter, habit streak badges & instant self-renewal door unlock.", td_style),
            Paragraph("<b>Higher Lifetime Value (LTV):</b> Boosts member renewal retention by up to 35%.", td_accent)
        ],
    ]

    leak_table = Table(leak_table_data, colWidths=[150, 228, 145])
    leak_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(leak_table)

    story.append(PageBreak())

    # =========================================================
    # PAGE 2: PILLARS 1, 2, 3 — SECURITY, RECEPTION, ONBOARDING
    # =========================================================
    story.append(Paragraph("2. The Complete FitMe Gym Ecosystem (10 Operational Superpowers)", h1_style))
    story.append(Paragraph(
        "FitMe equips your health club with 10 integrated operational pillars. Here is how each module makes your gym run smoother, safer, and more profitably:",
        body_style
    ))

    # Pillar 1
    story.append(Paragraph("Pillar 1: Smart Biometric Barrier Gates & AI Face Recognition — Stop Unpaid Walk-ins", h2_style))
    story.append(Paragraph("• <b>ZKTeco SpeedFace-V5L [TI] Dual-Camera AI Terminal:</b> High-speed visible light and infrared facial detection with anti-spoofing; recognizes registered members instantly without vulnerable keypad PINs or shared RFID cards.", bullet_style))
    story.append(Paragraph("• <b>High-Speed Optical Turnstiles:</b> Barrier gate releases smoothly in <b><0.3 seconds</b> upon verified face, fingerprint, or smart card punch.", bullet_style))
    story.append(Paragraph("• <b>Automated Gate Access Enforcement:</b> The turnstile gate automatically stays locked for expired memberships, overdue balances, or off-peak members trying to enter outside their allotted hours.", bullet_style))
    story.append(Paragraph("• <b>Works Even When Internet Drops (Offline Buffer):</b> If gym internet or local Wi-Fi goes down, all member access logs queue locally on the gym PC with zero data loss, automatically syncing back to the cloud as soon as connection is restored.", bullet_style))
    story.append(Paragraph("• <b>Remote Reception Gate Release:</b> Front-desk receptionists can remotely trigger the gate relay or sound a hardware buzzer alert directly from the digital reception console.", bullet_style))
    story.append(Paragraph("• <b>Real-Time Gym Floor Headcount:</b> Live telemetry monitor shows gym management exactly who is inside the gym right now and tracks peak workout hours.", bullet_style))

    # Pillar 2
    story.append(Paragraph("Pillar 2: Frictionless Front Desk & Flexible Memberships — Fast Service & Instant Renewals", h2_style))
    story.append(Paragraph("• <b>3-Second Member Lookup:</b> Reception staff can pull up any member profile in seconds by typing their Name, Mobile Phone, NIC / Passport, or Member ID.", bullet_style))
    story.append(Paragraph("• <b>6 Core Membership Tiers:</b> Ready-to-use pricing packages including Monthly (Rs. 4,000), 3-Month Discounted (Rs. 11,000), 6-Month (Rs. 21,500), Couple Monthly (Rs. 7,500), 3-Person Family (Rs. 11,000), and Student Discount Plan (Rs. 3,500 with waived registration).", bullet_style))
    story.append(Paragraph("• <b>Automated Annual Registration Fee:</b> Automatically charges your yearly registration fee (Rs. 1,000 default) upon enrollment/renewal and automatically waives it (Rs. 0) for students.", bullet_style))
    story.append(Paragraph("• <b>Buddy & Family Account Linking:</b> Couples or family members can link to a single payer while each person enjoys their own face ID profile and mobile app.", bullet_style))
    story.append(Paragraph("• <b>Member Self-Renewal & Instant Door Unlock:</b> Expired members can renew directly from their phone, submit payment reference, and have turnstile access unblocked instantly.", bullet_style))
    story.append(Paragraph("• <b>Digital Membership Card & Thermal Receipts:</b> Members receive a smartphone membership pass with QR code, while front desk issues professional 80mm ESC/POS thermal payment receipts.", bullet_style))

    # Pillar 3
    story.append(Paragraph("Pillar 3: Clinical Health Screening & Digital Assessment Intake — High-End Onboarding", h2_style))
    story.append(Paragraph("• <b>Comprehensive Physical Activity Readiness Questionnaire (PAR-Q):</b> Digital intake questionnaires capturing medical history, cardiovascular screening, joint/bone pain, previous surgeries, and fitness objectives (Muscle Gain, Fat Loss, Rehab).", bullet_style))
    story.append(Paragraph("• <b>Sri Lankan Nutrition Assessment Form:</b> Screens member eating patterns, water intake, daily tea/coffee habits, supplement usage (Whey, Creatine, Pre-workout), digestion, and sleep hours.", bullet_style))
    story.append(Paragraph("• <b>Coach Review & Prescription Dashboard:</b> Coaches review pending assessments online, flag medical precautions, assign target caloric splits, and prescribe custom gym training routines.", bullet_style))

    story.append(PageBreak())

    # =========================================================
    # PAGE 3: PILLARS 4, 5, 6, 7 — TRAINING, DIET, VAULT, POS
    # =========================================================
    story.append(Paragraph("2. The Complete FitMe Gym Ecosystem (Continued)", h1_style))
    story.append(Paragraph(
        "FitMe seamlessly unites personal training, authentic local nutrition, client body transformations, and retail supplement sales:",
        body_style
    ))

    # Pillar 4
    story.append(Paragraph("Pillar 4: 400+ Exercise Library & Coach Routine Builder — Premium Coaching Experience", h2_style))
    story.append(Paragraph("• <b>Illustrated 400+ Exercise Database:</b> Visual anatomical muscle group diagrams highlighting primary and secondary muscles (Chest, Back, Arms, Quads, Hamstrings, Glutes, Calves, Core) with equipment filters (Barbells, Dumbbells, Cables, Machines, Bodyweight).", bullet_style))
    story.append(Paragraph("• <b>Custom Workout Routine Builder:</b> Coaches build multi-day training splits (Push/Pull/Legs, Upper/Lower, 4-Day Splits, Full Body) with customized sets, target reps, weight (kg/lbs), rest countdown timers, and Reps-in-Reserve (RiR).", bullet_style))
    story.append(Paragraph("• <b>Interactive In-Gym Workout Logger:</b> Members log actual weights and completed reps right on their smartphone during workouts, with automatic 1RM (One Rep Max) calculation and Personal Record (PR) tracking.", bullet_style))
    story.append(Paragraph("• <b>1-Click Coach Program Push:</b> Coaches assign personalized routines directly to client mobile screens with instant updates.", bullet_style))

    # Pillar 5
    story.append(Paragraph("Pillar 5: 200+ Sri Lankan Food Database & Habit Consistency Engine — Keep Members Loyal", h2_style))
    story.append(Paragraph("• <b>200+ Sri Lankan Food Database:</b> Curated local food items with exact lab-grade macronutrients (Calories, Protein, Carbs, Fats, Fiber) for Red Raw Rice, Samba Rice, Fish Ambul Thiyal, Dhal Curry (Parippu), Pol Sambol, Chicken Curry, Kottu Roti, Egg Hoppers, String Hoppers, Samaposha balls, Kurakkan Thalapa, etc.", bullet_style))
    story.append(Paragraph("• <b>Coach Fuel Targets & Quick Meal Logging:</b> Coaches set daily target Calories, Protein, Carbs, and Fat; members search local foods and log meals in under 10 seconds.", bullet_style))
    story.append(Paragraph("• <b>Hydration Water Counter:</b> Visual 8-glass daily water tracker on the member dashboard encouraging daily hydration compliance.", bullet_style))
    story.append(Paragraph("• <b>Gamified Habit Consistency Engine:</b> Real-time streak counter tracking consecutive days of gym workouts and nutrition logging.", bullet_style))
    story.append(Paragraph("• <b>Milestone Trophies & Badges:</b> Automated achievement badge unlocks (e.g., 'Century Club - 100 Workouts', 'Consistency Champion - 30 Days', 'Iron Lifter', 'Protein Master') driving community engagement and slashing member churn by up to 35%.", bullet_style))

    # Pillar 6
    story.append(Paragraph("Pillar 6: Biometric Body Composition & Before/After Transformation Vault — Visual Proof of Results", h2_style))
    story.append(Paragraph("• <b>Biometric Body Tracking:</b> Logs body weight trends, BMI, and estimated body fat percentage with visual progression graphs.", bullet_style))
    story.append(Paragraph("• <b>8-Point Tape Circumference Measurements:</b> Tracks Chest, Waist, Hips, Left Arm, Right Arm, Left Thigh, Right Thigh, and Calves over time.", bullet_style))
    story.append(Paragraph("• <b>Encrypted Before/After Transformation Vault:</b> Private, timestamped photo vault (Front, Side, Back poses) with side-by-side comparison tool for coaches and members. Protected cloud media serving guarantees member privacy.", bullet_style))

    # Pillar 7
    story.append(Paragraph("Pillar 7: Front-Desk Shake Bar & Supplement POS — Rapid Touchscreen Checkout", h2_style))
    story.append(Paragraph("• <b>Touchscreen Cashier Register:</b> High-speed checkout built for selling protein scoops, pre-workout drinks, bottled water, energy bars, gym straps, shaker bottles, and gym apparel.", bullet_style))
    story.append(Paragraph("• <b>5 Flexible Payment Modes:</b> Cash (with instant change calculator), Credit/Debit Card terminal, LankaQR / Direct Bank Transfer, Member Credit Tab, and <b>Koko Pay</b> (Buy Now, Pay Later in 3 interest-free installments).", bullet_style))
    story.append(Paragraph("• <b>Dual Financial & Stock Audit Controls:</b><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;1. <b>Cash Drawer Float Audit:</b> Tracks opening cash float, cash ins/outs, closing declared cash, and automatically flags cashier shortages.<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;2. <b>Stock Inventory Cycle Audit:</b> Physical inventory counting tool with shrinkage flags, restocking alerts, and retail margin analytics.", bullet_style))
    story.append(Paragraph("• <b>Product Management & ESC/POS Receipts:</b> Barcode-ready catalog, quick restock modal, admin item deletion, and instant 80mm thermal sales receipts.", bullet_style))

    story.append(PageBreak())

    # =========================================================
    # PAGE 4: PILLARS 8, 9, 10 — PAYROLL, FINANCIALS, PORTALS
    # =========================================================
    story.append(Paragraph("2. The Complete FitMe Gym Ecosystem (Continued)", h1_style))
    story.append(Paragraph(
        "FitMe provides enterprise administrative tools engineered specifically for Sri Lankan labor laws and gym financial governance:",
        body_style
    ))

    # Pillar 8
    story.append(Paragraph("Pillar 8: Sri Lankan Legal Payroll & Shift Scheduling — 100% EPF/ETF Compliant", h2_style))
    story.append(Paragraph("• <b>100% Sri Lankan Statutory Labor Compliance:</b> Automated statutory payroll calculations strictly compliant with Sri Lankan labor law: <b>Employee EPF (8%)</b>, <b>Employer EPF (12%)</b>, and <b>Employer ETF (3%)</b>, automatically computed and ledgered every month.", bullet_style))
    story.append(Paragraph("• <b>Shift Roster Engine:</b> Shift templates for Morning (05:00-12:00), Evening (15:00-21:00), Full Split Shifts, and Scheduled Rest Days with 1-click bulk monthly roster generation for all floor trainers and front-desk staff.", bullet_style))
    story.append(Paragraph("• <b>Sudden Absence Detection Alerts:</b> Background monitor compares scheduled shifts against biometric clock-ins; if a trainer or receptionist fails to punch in within <b>30 minutes</b> of shift start, an automated alert notifies gym management immediately.", bullet_style))
    story.append(Paragraph("• <b>Salary Advances & Thermal Signature Vouchers:</b> Front-desk issuance of employee salary advances with instant 80mm ESC/POS Thermal Advance Vouchers with employee signature line; auto-deducted from final monthly pay.", bullet_style))
    story.append(Paragraph("• <b>Personal Trainer (PT) Commission Tracking:</b> Tracks billable 1-on-1 personal training sessions per coach with clear revenue split calculations.", bullet_style))
    story.append(Paragraph("• <b>Itemized 80mm Thermal Salary Slips:</b> 1-click thermal printing of official monthly pay slips with Basic Salary, Overtime, PT Commissions, Gross Pay, 8% EPF, Advances Deducted, Employer 12% EPF, Employer 3% ETF, and Net Payable.", bullet_style))
    story.append(Paragraph("• <b>Bank & Labor Dept CSV Exports:</b> Instant export of monthly payroll ledger formatted for Sri Lankan commercial bank bulk transfers (Commercial Bank, Sampath, HNB, BOC) and Department of Labor EPF Form C returns.", bullet_style))

    # Pillar 9
    story.append(Paragraph("Pillar 9: Daily Financial Close & Petty Cash Cam — Total Cash Accountability", h2_style))
    story.append(Paragraph("• <b>Automated Daily End-of-Day (EOD) Financial Close:</b> Single consolidated report combining daily membership subscription collections, POS retail revenue, petty cash payouts, and net daily cash balance.", bullet_style))
    story.append(Paragraph("• <b>Club Operational Expense Tracking & 'Petty Cash Cam':</b> Front-desk staff can record operational expenses (cleaning supplies, repairs, electricity, hospitality) and upload receipt photos directly from their smartphone camera into the cloud ledger.", bullet_style))
    story.append(Paragraph("• <b>External Auditor CSV Export Suite:</b> 4 one-click financial CSV exports: (1) Financial Summary CSV, (2) Member Roster CSV, (3) Club Expense Ledger CSV, and (4) Staff Payroll & EPF/ETF Ledger CSV for seamless accounting handoff.", bullet_style))

    # Pillar 10
    story.append(Paragraph("Pillar 10: 5 Role-Specific Portals & High-Converting Gym Website — Digital Dominance", h2_style))
    story.append(Paragraph("• <b>5 Role-Based Digital Portals:</b><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;1. <b>Super Admin (Owner):</b> Executive KPIs, revenue analytics, plan builder, discount rules, staff roster, payroll finalization.<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;2. <b>Front Desk Receptionist:</b> 3-second search, fast intake, check-in monitor, POS register, cash drawer audit, receipt printing.<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;3. <b>Personal Trainer / Coach:</b> Client rosters, workout routine push, assessment evaluations, progress photo tracking.<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;4. <b>Gym Member Mobile Portal:</b> Workout logger, 200+ local food tracker, hydration, digital membership card, self-renewal.<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;5. <b>Public Showcase & Online Joining:</b> High-conversion Next.js 14 marketing portal highlighting club facilities, trainer bios, transparent pricing packages, and online member registration application form.", bullet_style))
    story.append(Paragraph("• <b>Enterprise Cloud Infrastructure:</b> Hosted on Docker containerized architecture (Render / PostgreSQL / Redis / Celery) with 99.9% uptime SLA, automated offsite database backups, and SSL encryption.", bullet_style))

    story.append(PageBreak())

    # =========================================================
    # PAGE 5: COMMERCIAL QUOTATION & HARDWARE BOM
    # =========================================================
    # Section 3: Commercial Quotation (100% Software-Only Lifetime — Zero Monthly Fees)
    story.append(Paragraph("3. Commercial Quotation: Software-Only Lifetime License (Zero Monthly Fees)", h1_style))
    story.append(Paragraph(
        "FitMe is delivered as a <b>100% Software-Only Perpetual Lifetime License</b>. "
        "<b>No hardware purchase is required</b>. The system operates directly on your existing gym computers, laptops, tablets, and smartphones with <b>ZERO monthly subscription fees</b>:",
        body_style
    ))

    # Edition 1: Core Standard Software
    story.append(Paragraph("<b>TIER 1: FitMe Core Standard Edition (Software Only)</b>", h2_style))
    story.append(Paragraph("Complete digital front-desk, membership, and POS register for single-branch gyms.", body_style))

    tier_1_data = [
        [
            Paragraph("Software Edition & Scope", th_style),
            Paragraph("Modules & Capabilities Included", th_style),
            Paragraph("One-Time Lifetime Fee", th_style)
        ],
        [
            Paragraph("<b>FitMe Core Standard</b><br/><i>(Software Only)</i>", td_bold),
            Paragraph("• <b>Unlimited Members & Subscriptions:</b> 8 plan types, renewals, discount tracking, automated expiry alerts.<br/>"
                      "• <b>Front Desk Reception Portal:</b> 3-second quick search, fast member check-in, walk-in registration.<br/>"
                      "• <b>Point of Sale (POS) Cashier Register:</b> Retail drinks, supplements, snacks, instant change calculator.<br/>"
                      "• <b>Cash Drawer Float & Daily EOD Close:</b> Daily opening float, cash drawer reconciliation, petty cash tracking.<br/>"
                      "• <b>Existing Equipment Support:</b> Works on any existing Windows/Mac PC, laptop, or tablet. Works with any standard printer.<br/>"
                      "• <b>Data Migration:</b> Bulk migration of all your existing members from Excel/CSV included free.", td_style),
            Paragraph("<b>LKR 95,000</b><br/><i>(One-time payment)</i><br/><br/><font color='#059669'><b>Rs. 0 / month forever</b><br/>No monthly fees</font>", td_accent)
        ]
    ]

    tier_1_table = Table(tier_1_data, colWidths=[130, 255, 138])
    tier_1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(tier_1_table)
    story.append(Spacer(1, 5))

    # Edition 2: Professional All-Inclusive Software (Recommended)
    story.append(Paragraph("<b>TIER 2: FitMe Professional Enterprise Edition (Full 5-Role Software — Recommended)</b>", h2_style))
    story.append(Paragraph("The complete, high-converting fitness club ecosystem with coach tools, member self-service, Sri Lankan nutrition, and statutory payroll.", body_style))

    tier_2_data = [
        [
            Paragraph("Software Edition & Scope", th_style),
            Paragraph("Modules & Capabilities Included", th_style),
            Paragraph("One-Time Lifetime Fee", th_style)
        ],
        [
            Paragraph("<b>FitMe Professional Complete</b><br/><i>(Software Only)</i><br/><br/><font color='#059669'><b>★ BEST VALUE</b></font>", td_bold),
            Paragraph("• <b>Everything in Tier 1</b> (Full Membership, Front Desk, POS, Daily EOD Close, Excel Migration).<br/>"
                      "• <b>All 5 User Role Portals:</b> Super Admin (Owner), Front Desk, Coach Portal, Member Self-Service App & Public Website.<br/>"
                      "• <b>Sri Lankan Nutrition Database (200+ Foods):</b> Local rice & curry, kottu, hopper database with automated calorie & macro calculator.<br/>"
                      "• <b>Digital Assessment Forms:</b> Nutrition Assessment & Workout Assessment digital questionnaire with instant PDF export.<br/>"
                      "• <b>Sri Lankan Statutory Payroll:</b> Automated Employee 8% EPF, Employer 12% EPF, and Employer 3% ETF calculations, salary advances, and 1-click pay slips.<br/>"
                      "• <b>Member Gamification & Vault:</b> Habit streaks, achievement milestone badges, private transformation photo comparison vault.<br/>"
                      "• <b>1 Full Year Technical Support & Updates:</b> Remote assistance, system optimization, and training included.", td_style),
            Paragraph("<b>LKR 145,000</b><br/><i>(One-time payment)</i><br/><br/><font color='#059669'><b>Rs. 0 / month forever</b><br/>Lifetime Ownership</font>", td_accent)
        ]
    ]

    tier_2_table = Table(tier_2_data, colWidths=[130, 255, 138])
    tier_2_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(tier_2_table)
    story.append(Spacer(1, 5))

    # Optional Add-on for biometrics
    story.append(Paragraph("<b>OPTIONAL ADD-ON: Biometric Hardware Daemon Link</b>", h2_style))
    story.append(Paragraph(
        "If your gym already owns or later decides to add a biometric device (fingerprint or face terminal) or turnstile, "
        "we provide the <b>ZKBio Bridge Daemon integration</b> as an optional one-time add-on for <b>LKR 25,000</b> (No recurring fees).",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Payment milestones note
    story.append(Paragraph(
        "<b>Milestone Payment Terms:</b> 50% advance upon project confirmation &bull; 50% upon full deployment, Excel data migration & staff training.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 4: Hardware Independence
    story.append(Paragraph("4. Hardware Independence — Use Your Existing Gym Equipment", h1_style))
    story.append(Paragraph(
        "FitMe requires <b>NO specialized hardware purchases</b>. It runs seamlessly on standard office and personal devices already present in your gym:",
        body_style
    ))

    hw_data = [
        [
            Paragraph("Existing Gym Device", th_style),
            Paragraph("Compatibility & How FitMe Utilizes It", th_style),
            Paragraph("Hardware Cost to Gym", th_style)
        ],
        [
            Paragraph("<b>Front Desk PC or Laptop</b>", td_bold),
            Paragraph("Any standard PC or laptop running Windows, macOS, or Linux. Used for member intake, check-in search, POS cashier register, and daily reports.", td_style),
            Paragraph("<font color='#059669'><b>LKR 0</b><br/><i>(Use existing PC)</i></font>", td_accent)
        ],
        [
            Paragraph("<b>Staff & Coach Smartphones</b>", td_bold),
            Paragraph("Trainers and front-desk staff can use their Android or iPhone devices to review client rosters, log workouts, and check shift schedules.", td_style),
            Paragraph("<font color='#059669'><b>LKR 0</b><br/><i>(Use existing phones)</i></font>", td_accent)
        ],
        [
            Paragraph("<b>Member Smartphones / Tablets</b>", td_bold),
            Paragraph("Members access their personal portal, log Sri Lankan meals, and track progress photos directly on their own mobile browser without app store fees.", td_style),
            Paragraph("<font color='#059669'><b>LKR 0</b><br/><i>(Use member phones)</i></font>", td_accent)
        ],
        [
            Paragraph("<b>Receipt / Office Printer</b>", td_bold),
            Paragraph("Compatible with any existing 80mm or 58mm thermal receipt printer (USB/LAN/Bluetooth) or standard A4 office printer for reports and pay slips.", td_style),
            Paragraph("<font color='#059669'><b>LKR 0</b><br/><i>(Use existing printer)</i></font>", td_accent)
        ]
    ]

    hw_table = Table(hw_data, colWidths=[140, 245, 138])
    hw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(hw_table)

    story.append(PageBreak())

    # =========================================================
    # PAGE 6: ROI, ROADMAP & FORMAL ACCEPTANCE SIGN-OFF
    # =========================================================
    # Section 5: ROI
    story.append(Paragraph("5. Return on Investment (ROI) & Financial Payback Model", h1_style))
    story.append(Paragraph(
        "Based on performance metrics across active gyms with 250+ registered members, "
        "<b>FitMe pays for itself within 45 to 60 days</b> purely through automated leakage elimination:",
        body_style
    ))

    roi_data = [
        [
            Paragraph("Revenue Recovery & Cost Reduction Stream", th_style),
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
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, c_light]),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor("#D1FAE5")),
    ]))
    story.append(roi_table)
    story.append(Spacer(1, 6))

    # Section 6: Roadmap
    story.append(Paragraph("6. 10-Day Rapid Deployment Roadmap & Service Level Agreement (SLA)", h1_style))
    story.append(Paragraph(
        "Deployment is executed smoothly without interrupting active gym hours:",
        body_style
    ))

    roadmap_data = [
        [
            Paragraph("Timeline", th_style),
            Paragraph("Implementation Stage", th_style),
            Paragraph("Key Milestones & Operational Deliverables", th_style)
        ],
        [
            Paragraph("<b>Days 1 – 2</b>", td_bold),
            Paragraph("Cloud Provisioning", td_style),
            Paragraph("Spin up cloud database, configure security & SSL, bind custom domain (gym.lk), seed 8 membership tiers & Sri Lankan food database.", td_style)
        ],
        [
            Paragraph("<b>Days 3 – 4</b>", td_bold),
            Paragraph("Data Migration", td_style),
            Paragraph("Bulk import existing member records from Excel/CSV (names, NIC/passport, contact numbers, active plan status, expiry dates).", td_style)
        ],
        [
            Paragraph("<b>Days 5 – 6</b>", td_bold),
            Paragraph("Hardware Bridge", td_style),
            Paragraph("Install ZKBio Bridge Daemon on Gym PC, calibrate SpeedFace AI face terminal, wire turnstile relays, verify offline SQLite buffer queue.", td_style)
        ],
        [
            Paragraph("<b>Days 7 – 8</b>", td_bold),
            Paragraph("POS & Thermal Printers", td_style),
            Paragraph("Configure 80mm ESC/POS thermal printers, load retail supplement catalog, configure barcode scanners, test cash drawer reconciliation.", td_style)
        ],
        [
            Paragraph("<b>Days 9 – 10</b>", td_bold),
            Paragraph("Staff Training & Go-Live", td_style),
            Paragraph("Train front-desk staff & coaches on 5 role portals, conduct member face enrollment, activate official turnstile gate lockdown.", td_style)
        ],
    ]

    roadmap_table = Table(roadmap_data, colWidths=[75, 120, 328])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
    ]))
    story.append(roadmap_table)
    story.append(Spacer(1, 8))

    # Section 7: Formal Acceptance
    story.append(Paragraph("7. Acceptance & Authorization Sign-off", h1_style))
    story.append(Paragraph(
        "By signing below, the Client authorizes the deployment of the FitMe Gym Operating System under the terms and specifications outlined herein:",
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
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(sign_table)

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated proposal PDF at: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "FitMe_Gym_Proposal_and_Quotation.pdf"
    build_pdf(target)
