# 🏋️ Fit Me Fitness Club — Complete User Manual
### *"Train with Purpose & Move with Confidence"*
**Pitigala, Sri Lanka · Version 2026 · hellofitme@outlook.com · 070 762 7878**

---

> [!IMPORTANT]
> This manual covers **all features** of the Fit Me portal — from member self-service and coach portals, to back-office payroll, biometric hardware, and financial operations. It is organized by **user role**.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [User Roles & Access](#2-user-roles--access)
3. [Logging In & Navigation](#3-logging-in--navigation)
4. [Super Admin Dashboard](#4-super-admin-dashboard)
5. [Admin (Club Operations) Dashboard](#5-admin-club-operations-dashboard)
6. [Front Desk Dashboard](#6-front-desk-dashboard)
7. [Coach Dashboard](#7-coach-dashboard)
8. [Member Dashboard](#8-member-dashboard)
9. [Membership Plans & Pricing](#9-membership-plans--pricing)
10. [Point of Sale (POS) System](#10-point-of-sale-pos-system)
11. [Biometric Access & ZKBio Hardware](#11-biometric-access--zkbio-hardware)
12. [Staff Payroll & Attendance](#12-staff-payroll--attendance)
13. [Financial Operations & Reports](#13-financial-operations--reports)
14. [Assessment Forms](#14-assessment-forms)
15. [Nutrition Tracking (Sri Lankan)](#15-nutrition-tracking-sri-lankan)
16. [Workout & Progress Tracking](#16-workout--progress-tracking)
17. [Announcements & Communications](#17-announcements--communications)
18. [Public-Facing Features](#18-public-facing-features)
19. [API & Integrations Reference](#19-api--integrations-reference)
20. [Quick Reference & Keyboard Shortcuts](#20-quick-reference--keyboard-shortcuts)

---

## 1. System Overview

**Fit Me** is an enterprise-grade gym management platform purpose-built for **Fit Me Fitness Club, Pitigala**, Sri Lanka. It combines:

| Module | What It Does |
|--------|-------------|
| **Membership Management** | Subscriptions, plans, renewals, discount tracking |
| **Biometric Access Control** | ZKTeco turnstile integration (face, fingerprint, RFID) |
| **Role-Based Dashboards** | 5 roles: Super Admin, Admin, Front Desk, Coach, Member |
| **Point of Sale (POS)** | Gym bar drinks, supplements, snacks, gear |
| **Staff Payroll** | Shifts, attendance, EPF/ETF, advance deductions |
| **Sri Lankan Nutrition** | Local food database, meal logging, macros |
| **Assessment Forms** | Digital Nutrition & Workout Assessment (PDF equivalent) |
| **Financial Reporting** | Revenue, expenses, payroll CSV exports, EOD reports |
| **Public Website** | Contact forms, membership registration, testimonials |

### Technology Stack

```
Backend:  Django 6 (Python)
Frontend: Next.js 16 + Tailwind v4 (fitme-ui/)
Database: SQLite (dev) → PostgreSQL (prod)
Hardware: ZKBio CVAccess (turnstile) + Bridge Daemon
Auth:     django-allauth + RBAC Groups
Hosting:  Render (backend) + Vercel (frontend)
```

---

## 2. User Roles & Access

Every user is assigned exactly one role. The system automatically routes them to their dashboard on login.

| Role | Dashboard URL | Who Uses It | Key Permissions |
|------|--------------|-------------|-----------------|
| `super_admin` | `/dashboard/admin/` | Gym Owner / Director | **Full authority**: plan creation, data overrides, discount waivers, role management, payroll finalization |
| `admin` | `/dashboard/admin/` | Club Manager | Daily operations, attendance, reports, POS, member rosters. **Cannot** create plans or override subscription data |
| `front_desk` | `/dashboard/front-desk/` | Reception Staff | Member check-in queue, walk-in applications, biometric enrollment, POS receipt printing |
| `coach` | `/dashboard/coach/` | Trainers / PT Coaches | Athlete rosters, workout planning, nutrition guidance, assessment review |
| `member` | `/dashboard/member/` | Gym Members | Personal portal, body stats, food log, attendance streak, active pass |

> [!NOTE]
> Demo credentials: `admin` / `fitme123!`, `frontdesk` / `fitme123!`, `coach_kamal` / `fitme123!`, `member_kasun` / `fitme123!`

---

## 3. Logging In & Navigation

### Accessing the Portal

1. Navigate to `http://your-domain.com/login/` (or `/user/login/`)
2. Enter your **username** and **password**
3. The system **automatically redirects** you to your role dashboard

### URL Structure

| URL | Purpose |
|-----|---------|
| `/dashboard/` | Auto-redirect based on role |
| `/dashboard/admin/` | Super Admin & Admin panel |
| `/dashboard/front-desk/` | Front desk operations |
| `/dashboard/coach/` | Coach portal |
| `/dashboard/member/` | Member self-service |
| `/pos/` | Point of Sale register |
| `/register/` | Public membership registration form |
| `/receipt/<id>/` | Thermal receipt viewer (printable) |
| `/admin/` | Django admin panel (Super Admin only) |

### Password Reset

1. Click **"Forgot Password?"** on the login page
2. Enter your registered email address
3. Check email for reset link (valid for 24 hours)
4. Click link → set new password

---

## 4. Super Admin Dashboard

**URL:** `/dashboard/admin/`  
**Access:** `super_admin` role (+ `is_superuser`)

The Super Admin dashboard is the **master control center** of Fit Me. It contains all Admin features **plus** exclusive controls.

### 4.1 Key Metrics Panel

At the top of the dashboard you'll see live counters:

| Metric | Description |
|--------|-------------|
| **Active Members** | Members with a valid, active subscription today |
| **Expiring Soon** | Subscriptions expiring within 7 days |
| **Today's Revenue** | All membership payments collected today |
| **Monthly Revenue** | Total membership revenue this calendar month |
| **On Floor Now** | Members who punched in and are currently in the gym |
| **Staff Present** | Staff members on an active shift |

### 4.2 Member Roster

- View all members, filter by status (active, expired, pending)
- Click any member to view **full profile** including:
  - Personal info, NIC/Passport, blood group, medical conditions
  - Current subscription details and payment history
  - Biometric PIN and hardware access status
  - Body check-in history
  - Assigned coach and training program

#### Member Actions (Super Admin Exclusive)
- **Toggle Biometric Access** — Revoke or restore turnstile access
- **Override Subscription** — Manually change status, dates, or amount
- **Assign Coach** — Link a member to a specific trainer
- **Assign Program** — Set their active gym training program
- **Reset Password** — Force password reset for any user
- **Toggle Active/Inactive** — Disable/enable login for a user

### 4.3 Plan Builder (Super Admin Exclusive)

**Create / Edit Membership Plans:**

1. Scroll to **"Membership Plans"** section
2. Click **"+ Create New Plan"**
3. Fill in:
   - **Plan Name** (e.g., "Monthly Package")
   - **Plan Type** — choose from standard membership types
   - **Monthly Price (LKR)** — effective payable amount
   - **Original Price** — displayed for discount showing
   - **Discount Amount** — promotional reduction shown on receipts
   - **Registration Fee** — yearly admission fee (Rs. 0 for students)
   - **Duration Days** — validity period
   - **Max Members** — 1 for individual, 2 for Couples, 3 for Family
   - **Entry Time Window** — optional biometric access hours (e.g. 06:00–22:00)
   - **Active/Inactive** — hide from front desk while inactive
4. Click **"Save Plan"**

> [!TIP]
> To run a temporary promotion, update "Original Price" and "Discount" fields — these print on receipts as a crossed-out price showing savings.

### 4.4 Subscription Overrides & Concessions (Super Admin Exclusive)

For billing adjustments, custom discounts, or granting complimentary passes:

1. Navigate to **2. Members & Access** (`#tab-admin-members`)
2. In the Registered Member Directory, click **"Data Override"** (`fa-sliders-h`) next to the member's subscription
3. The **Master Data Override: Subscription** modal will open with the **Special Concession & Fee Waiver** engine:
   - **🎁 100% Free (Full Off)**: 1-click preset that zeroes the payable amount (`LKR 0.00`), sets the status to Active (unlocked at turnstile), selects Management Comp, and generates an official complimentary voucher.
   - **🏷️ 50% Off / -Rs. 1,000 Off**: Instant percentage or flat discount reduction.
   - **Concession Payment Settlement**:
     - **Pending Front Desk Counter Billing (Default & Recommended)**: Concession is approved, subscription is set to *Pending Payment*, and the turnstile remains locked. The member pays the remaining balance at the front desk counter via **Record Payment / Quick Renew**, where the receptionist collects the net balance and unlocks the gate.
     - **Cash Collected Now by Admin**: Super Admin received the cash at their desk; arms turnstile and issues receipt immediately.
   - **Reason Category (Mandatory)**: Select *VIP / Brand Ambassador*, *Staff Perk*, *Management Comp*, *Hardship*, or *Member Retention*.
   - **Live Calculation**: Displays Standard Plan Price, Savings Badge, and Net Payable.
4. Click **"Apply Data Override"** to save to the **Membership Discount Audit** ledger.

### 4.5 Discount & Complimentary Pass Auditing

All concessions are permanently tracked in the **Membership Discount Audit** log (`#tab-admin-audit` &bull; **Concessions & Waivers** and `/admin/membership/membershipdiscountaudit/`):

| Field | Purpose |
|-------|---------|
| **Discount Type** | Full Waiver (100% Free), Percentage %, or Flat LKR |
| **Original Price vs Payable** | List price before discount vs net amount collected (or remaining balance due) |
| **Settlement Status** | *Comped Free Pass*, *Settled @ Counter (Receipt #)*, or *Pending Front Desk Billing* |
| **Reason Category** | VIP/Sponsor, Staff Perk, Management Comp, Hardship, Retention |
| **Authorized By** | Super Admin username who signed off on the concession |
| **Justification** | Written business rationale |

### 4.6 User & Role Management

Navigate to **Admin → Users** (`/dashboard/admin/users/`):

- **Create New User** — add staff, coaches, or members manually
- **Update Role** — change group assignment (super_admin, admin, front_desk, coach, member)
- **Toggle Active** — disable/enable user login
- **Reset Password** — set a temporary password
- **Audit: Align Roles** — auto-fix inconsistent role/group assignments

### 4.7 Training Programs

Manage the gym's program catalog:

- **Create Program** with: title, category (Hypertrophy/Fat Loss/Strength/HIIT/Calisthenics/PT), difficulty (Beginner/Intermediate/Advanced), duration weeks, sessions/week, description, key features
- **Edit** or **Delete** existing programs
- Programs can be **assigned to members** by coaches and admins

### 4.8 Announcements

Post gym-wide broadcasts:

1. Click **"Post Announcement"**
2. Enter title, content, and priority:
   - **Info** — general notices (blue)
   - **Warning** — operational notices (yellow)
   - **Critical** — urgent/important (red)
3. Announcements appear on all role dashboards

### 4.9 Testimonials Management

- **Toggle visibility** of member transformation stories
- Stories include: before/after photos, weight loss/muscle gain data, duration, and member quote

### 4.10 Staff Operations

See Section 12 for full payroll documentation.

Super Admin exclusive actions:
- **Finalize Payroll** — lock a monthly payroll ledger (no more edits)
- **Adjust Payroll** — manually override any payroll line item with reason
- **Issue Salary Advance** — record mid-month cash/bank advance (auto-deducted from payroll)
- **Generate Payroll Thermal Slip** — printable 80mm salary slip

---

## 5. Admin (Club Operations) Dashboard

**URL:** `/dashboard/admin/`  
**Access:** `admin` role

The Admin shares the same dashboard URL as Super Admin but has **reduced permissions**. Plan creation, subscription overrides, and user role changes are locked.

### 5.1 Daily Operations

**Member Lookup (Front Desk Quick Search):**
1. Type a name, username, phone, or biometric PIN in the search bar
2. Results load instantly via API
3. Click a member to view status, active pass details, and entry log

**Record Payment:**
1. Go to member profile → **"Record Payment"**
2. Select plan, enter amount paid, choose payment method:
   - Cash at Counter
   - Card / POS Machine
   - Bank Transfer
   - Online Payment
3. System auto-generates a **thermal receipt** (FM-RCP-YYYY-XXXX format)
4. Receipt includes: member name, plan, validity dates, line items, payment breakdown

### 5.2 Applications Queue

Walk-in and online membership applications appear here:

| Column | Meaning |
|--------|---------|
| Applicant Name | Full name from registration form |
| Plan Requested | Desired membership package |
| Applied At | Timestamp of application |
| Status | Pending / Approved / Rejected |

**Approve Application:**
1. Click the application
2. Review 8 sections: personal info, emergency contact, plan, goals, medical, trainer need, payment, T&C
3. Click **"Approve"** → system auto-creates member account + subscription
4. Member receives email with login credentials

**Reject Application:**
1. Click **"Reject"** and enter rejection reason
2. Application status updates; no account created

### 5.3 Staff Attendance Management

- **Clock Staff In/Out** — manual attendance entry by admin
- **View Today's Roster** — see all on-floor and off-floor staff
- **Resolve Absence Alerts** — acknowledge sudden departure alerts

### 5.4 Absence Alerts

When a staff member **leaves the floor unexpectedly** (without an approved leave), a critical alert is triggered:
- Alert shows: staff name, departure time, minutes off-floor
- Admin clicks **"Resolve"** and adds notes (e.g., "Personal errand, approved verbally")

### 5.5 Financial Reports

**Available Exports (CSV):**

| Report | Content |
|--------|---------|
| **Financial CSV** | All membership payments by date range |
| **Members CSV** | Full member roster with plan and status |
| **Expenses CSV** | OPEX expense ledger |
| **Payroll CSV** | Staff net salary breakdown |

**End-of-Day (EOD) Report:**
- Navigate to `/dashboard/admin/reports/eod/`
- Shows: today's revenue, payment methods breakdown, new members, renewals, POS sales
- Printable format for end-of-shift reconciliation

---

## 6. Front Desk Dashboard

**URL:** `/dashboard/front-desk/`  
**Access:** `front_desk` role

Designed for reception staff managing the gym entrance.

### 6.1 Member Quick Lookup

1. Type member name, phone, PIN, or username in the search box
2. Card appears with:
   - Member photo
   - Active subscription status and days remaining
   - Biometric PIN
   - Entry/exit history
3. **"Ping Member"** — send a notification to the member's portal
4. **"Resend Invite"** — resend login credentials email

### 6.2 New Walk-In Registration

Click **"+ New Application"** to open the 8-section registration form:

| Section | Fields |
|---------|--------|
| 1. Personal Info | Full name, email, phone, DOB, gender, NIC/Passport, address |
| 2. Emergency Contact | Name, relationship, phone |
| 3. Payment Plan | Desired plan, duration, start date |
| 4. Fitness Goals | Primary goal selection |
| 5. Medical | Conditions, medications, blood group |
| 6. Trainer Need | Personal trainer required? Preferred coach? |
| 7. Payment | Admission fee, monthly fee, discount, total, payment method |
| 8. Terms | Agreement checkbox |

After submission, application goes into the **Pending** queue for admin approval.

### 6.3 Biometric Enrollment

After a member's subscription is approved:

1. Open their profile → **"Enroll Biometrics"**
2. Click **"Enroll Fingerprint"** — triggers 3-tap enrollment on turnstile terminal
3. Click **"Upload Face Photo"** — uploads member photo to ZKTeco face recognition
4. Member receives a unique **biometric PIN** (auto-assigned, 4 digits)

> [!NOTE]
> The turnstile terminal IP is `192.168.1.23`. Enrollment commands are sent via the ZKBio bridge daemon and executed on the hardware in real-time.

### 6.4 POS Sales at Front Desk

Front desk staff can process sales:

1. Navigate to `/pos/` or click **"POS Register"**
2. Add products by clicking category tiles, then item tiles
3. Set quantity for each item
4. Select customer (member lookup or "Walk-in")
5. Enter payment method and amount received
6. Click **"Complete Sale"** — system prints receipt and deducts stock

### 6.5 Receipt Printing

- All membership receipts: `/receipt/<id>/` — **optimized for 80mm thermal printer**
- Click **"Print"** or use browser print (Ctrl+P)
- Receipt shows: Fit Me logo, member name, plan, line items, payment breakdown, PIN, validity dates

---

## 7. Coach Dashboard

**URL:** `/dashboard/coach/`  
**Access:** `coach` role

### 7.1 Athlete Roster

See all members **assigned to you** as their coach:
- Name, photo, plan, last check-in, body stats
- Days since last workout log
- Active program assigned

### 7.2 Assessment Review Queue

When members submit **Nutrition** or **Workout Assessments**, they appear here:

1. Click **"Review"** on a pending assessment
2. Read all 12 sections of the member's self-report
3. Fill in your **Coach Plan**:
   - For Nutrition: daily calorie target, protein (g), carbs (g), fat (g), water (ml), plan notes
   - For Workout: training days/week, session duration, cardio recommendation, assigned program, plan notes
4. Click **"Submit Review"** — member's assessment status updates to "Reviewed"

### 7.3 Meal Review

If a member logs a meal for coach review:
1. Meal appears in coach queue
2. Coach clicks **"Approve"** or **"Suggest Changes"** with feedback notes

### 7.4 Workout Logging (on behalf of member)

Coaches can log workout sessions for members:
- Exercise name, sets, reps, weight (kg), session name, notes

### 7.5 Body Measurements Logging

Record monthly check-in measurements:
- Weight (kg), body fat %, muscle mass (kg), waist, chest circumference
- Front and side progress photos (uploaded)

### 7.6 Assign Programs & Coaches

- **Assign Training Program** — select from the gym's program catalog
- **Assign Coach** — transfer a member to another coach (Super Admin/Admin can also do this)

### 7.7 Set Nutrition Targets

Set personalized macros for a member:
- Calorie target, protein (g), carbs (g), fat (g)

---

## 8. Member Dashboard

**URL:** `/dashboard/member/`  
**Access:** `member` role

### 8.1 Active Pass Card

At the top: your current gym pass showing:
- Plan name
- Valid from → valid until dates
- Days remaining
- Current status (Active / Expiring Soon / Expired)
- Your unique **biometric PIN**
- Quick **"Self-Renew"** button

### 8.2 Sri Lankan Fuel Rings

Daily nutrition summary displayed as **rings** (inspired by Apple Activity rings):

| Ring | What It Tracks |
|------|---------------|
| 🟢 Protein | Grams consumed vs. your daily target |
| 🔵 Carbs | Grams consumed vs. target |
| 🟡 Fat | Grams consumed vs. target |
| 💧 Water | Milliliters logged vs. daily goal |

### 8.3 Food Logging

**Log a Meal:**
1. Click **"+ Log Meal"** or **"Quick Meal"**
2. Search the **Sri Lankan food database** (rice, curries, hoppers, kottu, etc.)
3. Enter portion size and meal timing (breakfast, lunch, dinner, snack, pre-workout, post-workout)
4. Save — macros auto-calculate and update your rings

**Log Water:**
1. Click **"+ Add Water"**
2. Select quick preset (150ml, 250ml, 500ml) or enter custom ml
3. Water ring updates immediately

### 8.4 Workout Logging

1. Click **"+ Log Workout"**
2. Select workout session name (Push Day, Pull Day, Legs, etc.)
3. Add exercises: name, sets, reps, weight (kg)
4. Add notes
5. Save — coach can view your logs

### 8.5 Body Measurements

Track your physical progress:
- Log weight, chest, waist, biceps, thighs circumference (cm)
- View historical chart showing your progress over time

### 8.6 Attendance Streak

Shows your **gym visit streak**:
- Days visited this week
- Total visits this month
- All-time total visits
- Last entry/exit timestamp

### 8.7 Assessment Forms

**Submit Nutrition Assessment:**
1. Click **"Nutrition Assessment"**
2. Fill 12 sections: personal info, goals, diet history, activity level, food preferences, current eating habits, supplements, medical conditions, sleep & stress
3. Submit — assigned coach receives it for review
4. Once reviewed, coach's personalized nutrition plan appears in your portal

**Submit Workout Assessment:**
1. Click **"Workout Assessment"**
2. Fill 8 sections: goals, gym history, physical measurements, equipment access, lifestyle/recovery, injuries, exercise preferences
3. Submit — coach reviews and creates your personalized training plan

### 8.8 My Programs

View your **currently assigned training program**:
- Program title, category, difficulty
- Duration (weeks), sessions per week
- Description and key features

### 8.9 Self-Renewal

1. Click **"Renew Pass"** on the member dashboard
2. System shows current plan and price
3. Submit renewal request — front desk/admin processes payment and activates

### 8.10 Partner / Buddy Membership

For **Couples** or **Family** plans, secondary members can see their linked subscription:
- Primary member name
- Shared plan details
- Individual biometric PINs

---

## 9. Membership Plans & Pricing

### 9.1 Current Plans (LKR) — Effective from 27th April 2026

| Package | Original Price | Discount | **Payable** | Duration | Members | Reg. Fee |
|---------|---------------|----------|-------------|----------|---------|----------|
| Monthly Package | Rs. 4,000 | — | **LKR 4,000** | 30 Days | 1 | LKR 1,000 |
| 3 Months Package | Rs. 12,000 | Rs. 1,000 | **LKR 11,000** | 90 Days | 1 | LKR 1,000 |
| 6 Months Package | Rs. 24,000 | Rs. 2,500 | **LKR 21,500** | 180 Days | 1 | LKR 1,000 |
| Couple Monthly | Rs. 8,000 | Rs. 500 | **LKR 7,500** | 30 Days | 2 | LKR 1,000 |
| 3-Person Family | Rs. 12,000 | Rs. 1,000 | **LKR 11,000** | 30 Days | 3 | LKR 1,000 |
| Student Package | Rs. 3,500 | — | **LKR 3,500** | 30 Days | 1 | **FREE** |

> [!IMPORTANT]
> - **Student package**: Strictly for ages **18 and under** only. When a student turns 19, they must upgrade to a general package.
> - **Registration fee**: LKR 1,000 applies for **all new members** (except students). Existing members renewing pay only the package fee.


### 9.2 Personal Coaching Add-On

- Standard coaching fee: **LKR 7,000/month** (on top of membership)
- Coach commission per dedicated PT athlete: **LKR 4,000/month** (paid from coaching fee)
- Add-on appears as a separate line item on receipts

### 9.3 Couples & Family Plans

When using Couples (2 members) or Family (3 members) plans:
1. Primary member is enrolled first with the full plan
2. Admin links the secondary/tertiary members via **"Link Partner"**
3. Each member gets their **own unique biometric PIN**
4. All members share the same subscription validity period

---

## 10. Point of Sale (POS) System

**URL:** `/pos/`  
**Access:** `front_desk`, `admin`, `super_admin`

### 10.1 POS Register Interface

The POS screen is organized as:

```
[Category Tiles] → [Product Grid] → [Cart / Order Summary] → [Checkout]
```

**Product Categories:**
- Drinks (water, energy drinks, protein shakes)
- Supplements (protein powder scoops, creatine, pre-workout)
- Snacks (protein bars, nuts, fruits)
- Gear (gloves, belts, resistance bands)

### 10.2 Processing a Sale

1. **Select Category** — click a category tile on the left
2. **Add Products** — click product tiles; they appear in the cart
3. **Adjust Quantity** — use +/- buttons in the cart
4. **Select Customer** — type to search members, or leave as "Walk-in Customer"
5. **Apply Discount** — enter a flat LKR discount if applicable
6. **Select Payment Method**:
   - Cash
   - Credit/Debit Card (POS Machine)
   - Koko Pay (Buy Now, Pay in 3)
   - Bank Transfer / QR Pay
   - Member Account Tab
7. **Enter Amount Received** — change is auto-calculated
8. **Complete Sale** — click "Process Sale"

System automatically:
- Generates a receipt number: `FITME-POS-YYYYMMDD-XXXX-ABCD`
- Deducts stock quantities from inventory
- Records cashier name and timestamp

### 10.3 Stock Management

**Dashboard Widgets:**
- **Low Stock** — products at or below their threshold (warning badge)
- **Missing Stock** — products flagged from previous audit with discrepancies
- **Total Inventory Value** — cost value and retail value of all stock
- **Recent Sales** — last 15 transactions with receipt numbers

### 10.4 Inventory Audit

Periodically reconcile physical stock vs. system records:

1. Click **"Conduct Stock Audit"** on a product
2. Enter the **physical count** (units you actually counted on shelf)
3. Select **reason** for any discrepancy:
   - Missing / Unexplained Stock Loss
   - Physical Count Adjustment
   - Damaged or Expired Stock
   - Suspected Loss / Theft
   - Supplier Invoice Discrepancy
   - Gym Bar / Coach Demo Sample
4. Select **action taken**:
   - Stock Level Adjusted
   - Flagged as Missing (Pending Review)
   - Reconciled & Closed
5. System calculates **financial variance** (units × cost price)
6. Products with discrepancies are flagged with a warning badge

### 10.5 Cash Drawer Audit

At the end of each shift, balance the cash drawer:

1. Click **"Cash Drawer Audit"**
2. Enter **Opening Float** (starting cash in drawer)
3. System auto-fetches **Recorded Cash Sales** total for the shift
4. Enter **Physical Cash Counted** in the till
5. System calculates discrepancy:
   - **Balanced** — exact match ✅
   - **Shortage** — less cash than expected ⚠️
   - **Overage** — more cash than expected (possible entry error)
6. Add notes and save

### 10.6 Refunds & Voids

- **Void** a sale (same-session error) — changes status to "Voided"
- **Refund** a completed sale — changes status to "Refunded"
- Both preserve the original receipt number for audit trail

---

## 11. Biometric Access & ZKBio Hardware

### 11.1 Hardware Setup

| Component | Details |
|-----------|---------|
| **Device** | ZKTeco Biometric Turnstile Controller |
| **Device IP** | `192.168.1.23` |
| **Service** | ZKBio CVAccess (localhost:8098) |
| **Cloud Link** | LiveU Cloud (via Cloudflare Tunnel) |
| **Bridge Daemon** | Node.js script: `scripts/zkbio_bridge_daemon.py` |

### 11.2 Member Biometric Profile

Each member has a **BiometricProfile** linked to their account:

| Field | Description |
|-------|-------------|
| **ZK PIN** | Unique 4-digit hardware PIN (auto-assigned 1001+) |
| **RFID Card Number** | Physical card number (optional) |
| **Face Enrolled** | ✅ Face template on terminal |
| **Fingerprint Enrolled** | ✅ Fingerprint on terminal |
| **Sync Status** | Pending / Synced / Failed / Revoked |
| **Disabled** | Access revoked (expired subscription / suspended) |

### 11.3 Verification Modes

Members can authenticate at the turnstile using:

| Mode | Method |
|------|--------|
| **Face Recognition** | Default — primary biometric |
| **Fingerprint** | Secondary option |
| **RFID Card** | Physical proximity card |
| **Manual Override (Buzzer)** | Staff-triggered 5-second relay pulse |

### 11.4 Real-Time Door Events

Every punch is recorded in the **Door Access Log**:

| Event | Meaning |
|-------|---------|
| **Entry Granted** | Member verified; turnstile opens |
| **Exit Granted** | Member punched out |
| **Access Denied** | Subscription expired or access revoked |
| **Anti-Passback Blocked** | Same member tried to re-enter within 60 seconds |

### 11.5 Anti-Passback Rule

- **60-second cooldown** between punches from the same PIN
- Prevents tailgating or multiple entries
- Blocked attempts are logged as `ANTI_PASSBACK`

### 11.6 Automatic Access Control

When a member's subscription **expires**:
1. The bridge daemon detects the expiry
2. The biometric profile is set to `disabled = True`
3. Next punch at the turnstile returns **Access Denied**
4. After renewal and activation, access is automatically restored

### 11.7 Remote Commands

Admins can issue remote commands to the turnstile from the dashboard:

| Command | Action |
|---------|--------|
| **Enroll Fingerprint** | Initiates 3-tap enrollment on terminal |
| **Upload Face Photo** | Pushes member photo to terminal |
| **Remote Buzz** | Pulses relay open for 5 seconds (door unlock) |
| **Revoke Access** | Deletes user from terminal |

Commands queue in the database and are executed by the bridge daemon polling cycle.

### 11.8 Staff Floor Attendance via Biometric

Staff members' punches are used for **attendance tracking**:
- Morning punch-in → sets `morning_in` timestamp
- Morning punch-out → sets `morning_out` timestamp
- Evening punch-in → sets `evening_in` timestamp
- Evening punch-out → sets `evening_out` timestamp
- Late arrival and overtime are auto-calculated

---

## 12. Staff Payroll & Attendance

### 12.1 Shift Types

| Shift Type | Hours |
|-----------|-------|
| **Full Split Shift** | 05:00–12:00 AND 15:00–21:00 |
| **Morning Shift** | 05:00–12:00 |
| **Evening Shift** | 15:00–21:00 |
| **Custom** | Admin-defined times |
| **Rest Day** | Scheduled off day |

### 12.2 Staff Work Schedule Setup

For each staff member, configure their master schedule:

1. Go to Super Admin panel → Staff → Work Schedules
2. Set for each day (Mon–Sun):
   - **Shift Type** (Full Split / Morning / Evening / Rest Day)
   - **Start and End Times**
   - **Active** toggle
3. Set **Base Salary** (LKR/month) and **Hourly Rate** (LKR/hour)
4. Set **EPF Eligible** (8% employee + 12% employer) and **ETF** (3% employer)
5. Enter **EPF Registration Number**

### 12.3 Roster Generation

Generate monthly shift schedules in bulk:

1. Click **"Generate Bulk Roster"**
2. Select staff member(s) and month
3. System creates a `StaffShift` record for every working day based on the master schedule
4. Individual shifts can be edited after generation

### 12.4 Leave Management

**Mark Approved Leave:**
1. Find the shift in the roster
2. Click **"Toggle Leave"** → shift status changes to `LEAVE`
3. Enter leave reason
4. Shift is excluded from late/absence calculations

### 12.5 Attendance Clocking

**Manual Clock-In (Admin):**
1. Go to Attendance → Clock Staff
2. Select staff member and session (Morning In/Out, Evening In/Out)
3. Optionally enter custom timestamp
4. Save — shift record updates

**Automatic (Biometric):**
- Staff punch at turnstile → system detects staff role → updates shift record

### 12.6 Late & Overtime Calculation

The system **automatically computes**:

| Calculation | Logic |
|-------------|-------|
| **Late Minutes** | Actual punch-in minus scheduled start (per session) |
| **Overtime Minutes** | Actual punch-out minus scheduled end |

### 12.7 Sudden Absence Alerts

When an on-shift staff member punches **out during working hours** without approved leave:
1. System triggers a **Sudden Absence Alert** (critical)
2. Alert appears on Super Admin/Admin dashboard
3. Shows: staff name, exit time, minutes off-floor
4. Admin resolves with notes

> [!WARNING]
> Unresolved absence alerts generate a penalty in the monthly payroll (default: 1.25× hourly rate per minute).

### 12.8 Salary Advance (Mid-Month Cash)

Issue a salary advance:

1. Click **"Issue Salary Advance"**
2. Select staff member
3. Enter amount (LKR)
4. Choose payout method: Cash from Till or Bank Transfer
5. Enter reason
6. System generates a unique voucher number: `FM-ADV-YYYY-XXXX`
7. Advance automatically deducted during monthly payroll run

### 12.9 Monthly Payroll Calculation

**Net Salary Formula:**
```
Net = (Base Salary + Overtime Pay + PT Commissions)
      − (Late Penalty + Absence Penalty + EPF 8% + Salary Advances)
```

**Gym Total Cost (Employer):**
```
Total Cost = Net Salary + EPF Employer 12% + ETF Employer 3%
```

**Payroll Run Steps:**

1. Click **"Recalculate Payroll"** for a specific month
2. System automatically aggregates:
   - All shift data for the month
   - Late minutes → penalty (at hourly rate)
   - Sudden absence penalties
   - PT athlete roster → commissions
   - Salary advances deducted
   - EPF/ETF contributions
3. Review the ledger
4. Click **"Adjust"** if manual corrections needed (with reason)
5. Click **"Finalize Payroll"** — locks the ledger permanently

### 12.10 Payroll Thermal Slip

Generate a printable 80mm salary slip for each staff member:
- URL: `/payroll/<ledger_id>/thermal-slip/`
- Shows full breakdown: gross, deductions, net, EPF/ETF

---

## 13. Financial Operations & Reports

### 13.1 Operating Expenses (OPEX)

Record all gym expenses:

1. Click **"+ Add Expense"**
2. Fill in:
   - **Title** — description of the expense
   - **Category**:
     - Facility & Building Rent
     - Electricity (CEB)
     - Water Utility
     - Equipment Maintenance & Repairs
     - Staff & Coach Payroll
     - POS Bar & Supplement Inventory
     - Hygiene & Cleaning Supplies
     - Internet & Security CCTV
     - Marketing, Social & Print Ads
     - Other Operational Expenses
   - **Amount** (LKR)
   - **Date**
   - **Payment Method** (Cash / Bank Transfer / Company Card)
   - **Receipt Reference** (bill/invoice number)
   - **Upload Receipt Photo or PDF** — scan of physical bill
3. Save

### 13.2 Revenue Tracking

All membership payment receipts are auto-tracked. System aggregates:
- Daily revenue
- Monthly revenue
- Revenue by payment method (cash, card, transfer, online)
- Revenue by plan type

### 13.3 CSV Exports

| Export | URL |
|--------|-----|
| Financial Report | `/dashboard/admin/reports/export-csv/` |
| Members Roster | `/dashboard/admin/reports/export-members-csv/` |
| Expenses Ledger | `/dashboard/admin/reports/export-expenses-csv/` |
| Payroll Report | `/dashboard/admin/reports/export-payroll-csv/` |

Each CSV downloads instantly with all relevant columns for Excel/Google Sheets.

### 13.4 End-of-Day (EOD) Report

URL: `/dashboard/admin/reports/eod/`

A daily close-out report showing:
- Total revenue collected today
- Breakdown by payment method
- New members enrolled
- Renewals processed
- POS sales total
- Outstanding pending payments

### 13.5 Thermal Receipts

All membership receipts are at `/receipt/<id>/` in **80mm thermal format**. Receipt contains:

```
┌─────────────────────────────┐
│  [Fit Me Logo]              │
│  Fit Me Fitness Club        │
│  Pitigala, Sri Lanka        │
├─────────────────────────────┤
│  Receipt: FM-RCP-2026-0042  │
│  Member: Kasun Perera       │
│  PIN: 1042                  │
├─────────────────────────────┤
│  Monthly Package       4,000│
│  90 Days (01/11–31/01)      │
│  Annual Registration   1,000│
│  Personal Coaching (1:1) 7,000│
├─────────────────────────────┤
│  TOTAL         LKR 12,000   │
│  PAID VIA: Cash             │
│  DATE: 20/10/2026 15:30     │
└─────────────────────────────┘
```

For **discounted/complimentary** receipts:
- Original price shown crossed out
- Discount line item with "Super Admin Concession" label
- Authorized by name on record

---

## 14. Assessment Forms

### 14.1 Nutrition Assessment

**Digital equivalent** of the "Fitness with Dhananjaya — Nutrition Assessment Form" PDF.

| Section | Content |
|---------|---------|
| 1. Personal Info | Name, DOB, age, gender, height, weight, phone, occupation |
| 2. Fitness Goals | Target weight, timeline, goal importance (0-10), goal checkboxes |
| 3. Weight & Diet History | Highest/lowest adult weight, previous diet plans, diet stop reasons |
| 4. Activity Level | Sedentary/Active/Very Active, work hours, sitting hours, daily steps |
| 5. Exercise History | Currently training, days/week, session duration, preferred time |
| 6. Food Preferences | Dietary type (omnivore/vegetarian/vegan), allergies, cultural restrictions, meal pattern |
| 7. Current Typical Day | Breakfast, lunch, dinner, snacks, water, tea/coffee, alcohol frequency |
| 8. Eating Habits | Outdoor eating frequency, stress/emotional/binge eating, meal skipping |
| 9. Supplements & Meds | Current supplements, medications, vitamin D/iron tests |
| 10. Medical Conditions | Conditions, digestive issues, hormonal, thyroid, PCOS, diabetes, BP |
| 11. Sleep & Stress | Sleep hours, quality, stress level (1-10), causes |
| 12. Member Notes | Additional free-text notes |

**Coach Review Adds:**
- Daily calorie target
- Protein (g), Carbs (g), Fat (g), Water (ml) targets
- Personalized nutrition plan notes

### 14.2 Workout Assessment

**Digital equivalent** of the "Fitness with Dhananjaya — Workout Assessment Form" PDF.

| Section | Content |
|---------|---------|
| 1. Personal Info | Name, DOB, height, weight, phone, email, occupation |
| 2. Fitness Goals | Target weight, timeline, motivation level (1-10), goal checkboxes |
| 3. Gym/Exercise History | Experience level, training frequency, session duration, previous training types |
| 4. Physical Assessment | Body fat %, body measurements, self-rated strength/endurance/flexibility (1-5), functional tests (push-ups, squats, plank) |
| 5. Equipment & Access | Gym access, home equipment, preferred gym area |
| 6. Lifestyle & Recovery | Sleep quality, stress level, recovery days, active rest activities |
| 7. Injuries & Medical | Current/past injuries, chronic conditions, physical limitations, medications |
| 8. Preferences | Exercises to avoid, preferred exercises, training split preference, cardio preference |

**Coach Review Adds:**
- Assigned training program
- Recommended training days/week and session duration
- Cardio recommendation
- Personalized workout plan notes

---

## 15. Nutrition Tracking (Sri Lankan)

### 15.1 Sri Lankan Food Database

The system includes a **local food database** (`nutrition_lk`) with Sri Lankan foods:
- Rice varieties (white, red, basmati)
- Curries (dhal, fish, chicken, jackfruit, drumstick)
- Bread (hoppers, string hoppers, roti, pol roti)
- Kottu roti, lamprais, pittu, kiri bath
- Fresh fruits, vegetables, coconut milk
- Street snacks (wade, samosa, isso wade)

### 15.2 Macro Tracking

Each food item contains:
- Calories (kcal)
- Protein (g)
- Carbohydrates (g)
- Fat (g)
- Fiber (g)

### 15.3 Logging a Meal

1. Navigate to Member Dashboard
2. Click **"+ Log Meal"**
3. Search food: type name (e.g., "rice", "dhal", "hopper")
4. Select portion size
5. Choose meal time
6. System calculates macros and updates your daily fuel rings

### 15.4 Water Tracking

- Click **"+ Add Water"**
- Quick presets: 150ml, 250ml, 500ml (glass, cup, bottle)
- Custom amount entry
- Daily target: set by coach (default: 2,000–3,000ml)

---

## 16. Workout & Progress Tracking

### 16.1 Workout Logging

Log individual exercise sets:

| Field | Example |
|-------|---------|
| Session Name | "Push Day", "Leg Day" |
| Exercise | "Bench Press", "Squat" |
| Sets | 4 |
| Reps | 10 |
| Weight | 60 kg |
| Notes | "Felt strong today" |

### 16.2 Body Measurements

Track circumference and composition over time:

| Metric | Unit |
|--------|------|
| Weight | kg |
| Chest | cm |
| Waist | cm |
| Biceps | cm |
| Thighs | cm |
| Body Fat % | % |

### 16.3 Body Check-Ins (Monthly)

Used by coaches and admins for **morph visualizer**:
- Weight (kg)
- Body fat %
- Muscle mass (kg)
- Waist, chest circumference
- Front and side progress photos
- Notes

### 16.4 Attendance Streak

Attendance is tracked via biometric punches:
- Visit streak: consecutive days attended
- Weekly visit count
- Monthly visit count
- All-time total visits

### 16.5 Training Programs Available

| Category | Example Programs |
|----------|-----------------|
| Hypertrophy & Muscle Build | 12-Week Mass Gain, PPL Split |
| Fat Loss & Shred | HIIT Combo, Metabolic Conditioning |
| Power & Strength | 5/3/1 Powerlifting, Starting Strength |
| HIIT & Conditioning | Tabata Protocol, CrossFit Style |
| Bodyweight & Calisthenics | Progressive Calisthenics, Pull-Up Program |
| 1-on-1 Personal Training | Custom coach program |

---

## 17. Announcements & Communications

### 17.1 Creating an Announcement

1. Super Admin/Admin → **"Post Announcement"**
2. Enter title and content
3. Select priority:
   - **Info** (blue) — general updates, schedule changes
   - **Warning** (orange) — operational notices, closures
   - **Critical** (red) — urgent messages, emergencies
4. Post — appears on all role dashboards immediately

### 17.2 Email Communications

The system includes a **Mailer module** (`/email/`) for:
- Sending bulk emails to member segments
- Renewal reminder emails
- Welcome emails for new members
- Password reset emails

### 17.3 Member Ping

From the Admin or Front Desk dashboard:
1. Open member profile
2. Click **"Ping Member"** — sends a notification to their portal
3. Used to alert members of expiring passes, overdue payments, etc.

### 17.4 Resend Invite

If a member hasn't received or needs a new login email:
1. Open member profile
2. Click **"Resend Invite"** — re-sends welcome email with login credentials

---

## 18. Public-Facing Features

### 18.1 Public Registration Form

**URL:** `/register/`

Walk-in members can fill out the **official 8-section registration form** without logging in. Applications land in the admin queue for approval.

### 18.2 Contact Form API

**URL:** `/api/public/contact/`

Website visitors can submit inquiries:
- Name, email, phone, subject, message
- All inquiries stored in **Contact Inquiry** table
- Admin can mark as resolved

### 18.3 Gym Proposal PDF

The `scripts/generate_proposal_pdf.py` script generates a **professional gym proposal PDF** for corporate or bulk membership inquiries.

---

## 19. API & Integrations Reference

### 19.1 REST API (v2)

**Base URL:** `/api/v2/`  
**Auth:** JWT Bearer Token (via `/api/v2/token/refresh`)  
**Docs:** `/api/v2/schema/ui/` (Swagger) or `/api/v2/schema/redoc/` (ReDoc)

| Endpoint Group | Base Path |
|----------------|-----------|
| Workout Routines | `/api/v2/routine/` |
| Exercises | `/api/v2/exercise/` |
| Nutrition Plans | `/api/v2/nutritionplan/` |
| Ingredients | `/api/v2/ingredient/` |
| Weight Entries | `/api/v2/weightentry/` |
| Measurements | `/api/v2/measurement/` |
| Trophies | `/api/v2/trophy/` |

### 19.2 ZKBio Bridge API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/zkbio/punches/` | POST | Receive real-time door punch events |
| `/api/zkbio/commands/poll/` | GET | Daemon polls for pending commands |
| `/api/zkbio/commands/<id>/ack/` | POST | Mark command as executed |
| `/api/zkbio/members/` | GET | Sync active member list to hardware |
| `/api/profile/update-photo/` | POST | Upload face photo for biometric enrollment |

**Authentication:** Bearer Token (`ZKBIO_BRIDGE_TOKEN` environment variable)

### 19.3 Dashboard APIs

All dashboard actions use internal JSON APIs:

| API | Method | Action |
|-----|--------|--------|
| `/dashboard/api/applications/create/` | POST | Submit new member application |
| `/dashboard/api/applications/<id>/approve/` | POST | Approve an application |
| `/dashboard/api/record-payment/` | POST | Record subscription payment |
| `/dashboard/api/desk/lookup/` | GET | Search member by name/PIN |
| `/dashboard/api/members/<id>/profile/` | GET | Full member profile JSON |
| `/dashboard/api/log-workout/` | POST | Log a workout session |
| `/dashboard/api/log-measurement/` | POST | Record body measurements |
| `/dashboard/api/log-water/` | POST | Add water intake |
| `/dashboard/api/payroll/recalculate/` | POST | Recalculate payroll for a month |
| `/dashboard/api/expenses/create/` | POST | Add OPEX expense |

### 19.4 Assessment APIs

| Endpoint | Method | Access |
|----------|--------|--------|
| `/api/assessments/nutrition/submit/` | POST | Member |
| `/api/assessments/workout/submit/` | POST | Member |
| `/api/assessments/nutrition/<id>/review/` | POST | Coach |
| `/api/assessments/workout/<id>/review/` | POST | Coach |
| `/api/assessments/pending/` | GET | Coach / Admin |
| `/api/assessments/my/` | GET | Member |

### 19.5 Health Check

**URL:** `/health/`  
**Method:** GET  
**Response:** `{"status": "ok", "database": "connected"}` (200) or 503 if DB error

---

## 20. Quick Reference & Keyboard Shortcuts

### Role Quick Navigation

| Who You Are | Your Dashboard | Key Actions |
|-------------|---------------|-------------|
| Super Admin | `/dashboard/admin/` | Plan Builder, User Roles, Payroll Finalize, Discount Audits |
| Admin | `/dashboard/admin/` | Applications, Payments, Reports, Staff Clock-In |
| Front Desk | `/dashboard/front-desk/` | Member Lookup, Walk-In Registration, Biometric Enrollment, POS |
| Coach | `/dashboard/coach/` | Athlete Roster, Assessment Review, Workout/Nutrition Plans |
| Member | `/dashboard/member/` | Food Log, Water, Workout Log, Body Measurements, Renew Pass |

### Common Receipt & Report URLs

| Function | URL |
|----------|-----|
| View Receipt | `/receipt/<id>/` |
| Payroll Slip | `/payroll/<ledger_id>/thermal-slip/` |
| Advance Voucher | `/advances/<advance_id>/thermal-voucher/` |
| EOD Report | `/dashboard/admin/reports/eod/` |
| Export CSV | `/dashboard/admin/reports/export-csv/` |

### Key Business Rules

| Rule | Value |
|------|-------|
| Registration Fee | LKR 1,000 (new members) |
| Student Age Limit | 18 years and under |
| Anti-Passback Cooldown | 60 seconds |
| EPF Employee Rate | 8% |
| EPF Employer Rate | 12% |
| ETF Employer Rate | 3% |
| Absence Alert Trigger | 20+ minutes off-floor without leave |
| Absence Penalty Multiplier | 1.25× hourly rate |
| Coach PT Commission | LKR 4,000 per dedicated athlete/month |
| Standard Coaching Fee | LKR 7,000/month add-on |
| Biometric PIN Range | 1001 – 9999 (auto-assigned) |

---

*Fit Me Fitness Club — Pitigala, Sri Lanka*  
*hellofitme@outlook.com | 070 762 7878*  
*New Town, Elpitiya Road, Pitigala, 80420*
