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

| Role | Dashboard URL | Access |
|------|--------------|--------|
| `super_admin` | `/fitme/dashboard/admin/` | Full system |
| `front_desk` | `/fitme/dashboard/front-desk/` | Member queue + payments |
| `coach` | `/fitme/dashboard/coach/` | Assigned members + nutrition |
| `member` | `/fitme/dashboard/member/` | Personal stats + digital ID |

## Getting Started

```bash
# Install dependencies
uv sync

# Run migrations
uv run --env-file .env python manage.py migrate

# Seed initial data
uv run --env-file .env python manage.py seed_fitme

# Create superuser & add to super_admin group
uv run --env-file .env python manage.py createsuperuser

# Start development server
uv run --env-file .env python manage.py runserver
```

Visit `http://127.0.0.1:8000/en/user/login` — login redirects to your role dashboard.

## Membership Plans (LKR)

| Plan | Price/Month | Members |
|------|-------------|---------|
| Individual | LKR 4,500 | 1 |
| Couples / Buddy | LKR 7,500 | 2 |
| Student | LKR 3,000 | 1 |
| Off-Peak | LKR 2,500 | 1 |

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
