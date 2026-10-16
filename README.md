# Fit Me — Smart Gym Management System

> **"Train with Purpose & Move with Confidence"**

Enterprise-grade gym management platform built on Django, featuring biometric access control, role-based dashboards, Sri Lankan nutrition tracking, and automated payroll.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6 (wger base) |
| Frontend Dashboards | Next.js 16 + Tailwind v4 (`fitme-ui/`) |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Hardware Bridge | Node.js (`zkbio-bridge-daemon/`) |
| Auth | django-allauth + RBAC Groups |

## Project Structure

```
fitme-portal/
├── wger/                    # Django backend
│   ├── membership/          # Membership plans, subscriptions, member profiles
│   ├── nutrition_lk/        # Sri Lankan food DB + meal logging
│   ├── habit/               # Workout streaks + coach habit pings
│   ├── payroll/             # Staff shifts, attendance, payroll, absence alerts
│   ├── zkbio_bridge/        # ZKBio CVAccess hardware bridge models
│   └── core/templates/fitme/dashboards/  # Role dashboards (HTML)
├── fitme-ui/                # Next.js frontend (future: React dashboards)
├── zkbio-bridge-daemon/     # Node.js local bridge for ZKBio hardware
├── settings/                # Django settings (main, global, local_dev)
└── db.sqlite3               # Dev database
```

## RBAC Roles

| Role | Dashboard URL | Permissions & Capabilities | Demo Credentials |
|------|--------------|----------------------------|------------------|
| `super_admin` | `/dashboard/admin/` | **Master Owner**: Full system authority, **Plan Builder** (+ Make New Plans), **Data Overrides** (manual date, expiry, and amount overrides; user role promotions). | `admin` / `fitme123!` |
| `admin` | `/dashboard/admin/` | **Club Admin (Operations)**: Daily floor management, turnstile punches, attendance, financial reports, POS sales, and member rosters. *(Plan creation and data overrides locked to Super Admin)*. | `admin_ops` / `fitme123!` |
| `front_desk` | `/dashboard/front-desk/` | Member queue, walk-in applications, biometric PIN enrollment & POS receipt printing. | `frontdesk` / `fitme123!` |
| `coach` | `/dashboard/coach/` | Assigned athlete rosters, biomechanics workout routines, and nutritional logs. | `coach_kamal` / `fitme123!` |
| `member` | `/dashboard/member/` | Athlete portal: Daily Sri Lankan fuel rings, water logging, attendance streaks, and active gym passes. | `member_kasun` / `fitme123!` |

## Deployment

For a 100% free production deployment using **Vercel + Render + Supabase**, see:
👉 **[Production Deployment Guide ($0 / Free Tier)](DEPLOYMENT_GUIDE.md)**

## Getting Started

```bash
# Install dependencies
uv sync

# Run migrations
uv run --env-file .env python manage.py migrate

# Seed initial data
uv run --env-file .env python manage.py seed_fitme

# Start development server
uv run --env-file .env python manage.py runserver
```

Visit `http://localhost:8000/login/` — login automatically routes to your role dashboard.

## Membership Plans (LKR) — Official Limited Time Packages

| Package | Original Price | Discount | Total Payable | Duration | Members | Registration Fee |
|---------|---------------|----------|---------------|----------|---------|------------------|
| **Monthly Package** | Rs. 4,000 | — | **LKR 4,000** | 30 Days | 1 Member | LKR 1,000 |
| **3 Months Package** | Rs. 12,000 | Rs. 1,000 | **LKR 11,000** | 90 Days | 1 Member | LKR 1,000 |
| **6 Months Package** | Rs. 24,000 | Rs. 2,500 | **LKR 21,500** | 180 Days | 1 Member | LKR 1,000 |
| **Couple Monthly Package** | Rs. 8,000 | Rs. 500 | **LKR 7,500** | 30 Days | 2 Members | LKR 1,000 |
| **3 Persons Family Monthly** | Rs. 12,000 | Rs. 1,000 | **LKR 11,000** | 30 Days | 3 Members | LKR 1,000 |
| **Students** | Rs. 3,500 | — | **LKR 3,500** | 30 Days | 1 Member | **FREE (No Reg Fee)** — *Ages 18 & under only* |

> **Registration Details:** Registration fee of Rs. 1,000 applies for all new members (except Students). The Student Package is strictly available for ages 18 and under; when turning 19, a general package is required. Effective from 27th April 2026.

> **Terms & Conditions:** Non-transferable, Non-refundable. Management reserves the right to make changes.
> **Contact:** `hellofitme@outlook.com` | `070 762 7878` | Pitigala, Sri Lanka

## ZKBio Bridge Daemon

```bash
cd zkbio-bridge-daemon
npm install
node index.js
```

Configure `.env` with `ZKBIO_API_URL`, `ZKBIO_TOKEN`, `CLOUD_API_URL`.

## Brand

- **Primary**: Neon Lime `#7BC900`
- **Background**: Carbon Black `#0B0D0E`
- **Fonts**: Bebas Neue (headings) + Inter (body) + Montserrat (stats)
