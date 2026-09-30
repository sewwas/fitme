# 🚀 Fit Me Portal — Production Deployment Guide ($0 / Free Tier)

This guide walks you through deploying the **Fit Me Fitness Club Portal** to production using 100% free cloud services, with zero monthly infrastructure cost.

---

## 🏛️ Recommended Architecture

```
                             [ End Users / Gym Members ]
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
       [ Frontend Website ]                              [ Backend API & Portal ]
         Vercel (Free)                                      Render (Free)
       fitmefitness.lk                                   api.fitmefitness.lk
                   │                                             │
                   │                                             ▼
                   │                                  [ PostgreSQL Database ]
                   │                                    Supabase (Free 500MB)
                   │                                             │
                   ▼                                             ▼
          [ Global Edge CDN ]                             [ Attendance Sync ]
            Instant Loading                              LiveU Cloud REST API
                                                      (Biometric Door Hardware)
```

| Component | Platform | Free Plan Allowance | Monthly Cost |
|---|---|---|:---:|
| **Frontend UI** | [Vercel](https://vercel.com) | 100GB bandwidth, free SSL, custom domain | **$0.00** |
| **Backend Web Service** | [Render](https://render.com) | 512MB RAM, Python/Docker runtime, auto-deploy from GitHub | **$0.00** |
| **Database** | [Supabase](https://supabase.com) | 500MB PostgreSQL, auto-backups, Web SQL editor | **$0.00** |
| **Uptime / Keep-Alive** | [cron-job.org](https://cron-job.org) | Unlimited HTTP pings every 10 min (prevents free sleep) | **$0.00** |
| **Hardware Cloud Sync** | [LiveU Cloud](https://attapi.liveucloud.com) | Managed turnstile cloud attendance sync | **$0.00** |

---

## 📋 Step-by-Step Setup

### Step 1: Create Free PostgreSQL Database on Supabase

1. Go to **[supabase.com](https://supabase.com)** and create a free account.
2. Click **New Project**:
   - **Name:** `fitme-production`
   - **Database Password:** *(Choose a strong password and save it)*
   - **Region:** Choose **Singapore** or **Mumbai** (closest to Sri Lanka for lowest latency).
3. Once created, go to **Project Settings** ➔ **Database** ➔ **Connection Parameters**:
   - **Host:** e.g. `db.xxxxxxxxxxxx.supabase.co`
   - **Database:** `postgres`
   - **Port:** `5432`
   - **User:** `postgres`
   - **Password:** `[Your Supabase Password]`

---

### Step 2: Deploy Backend to Render

1. Go to **[render.com](https://render.com)** and sign in with GitHub.
2. Click **New +** ➔ **Web Service**.
3. Select the repository: `sewwas/fitme`.
4. Render will automatically detect the provided `render.yaml` blueprint, or you can fill in:
   - **Name:** `fitme-backend`
   - **Region:** Singapore
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput
     ```
   - **Start Command:**
     ```bash
     gunicorn wger.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```
5. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `DJANGO_SETTINGS_MODULE` | `settings.main` |
   | `DJANGO_DEBUG` | `False` |
   | `SECRET_KEY` | *(Generate a long random string or let Render generate it)* |
   | `ALLOWED_HOSTS` | `.onrender.com,fitmefitness.lk,localhost,127.0.0.1` |
   | `DJANGO_DB_ENGINE` | `django.db.backends.postgresql` |
   | `DJANGO_DB_HOST` | `db.xxxxxxxxxxxx.supabase.co` |
   | `DJANGO_DB_DATABASE` | `postgres` |
   | `DJANGO_DB_USER` | `postgres` |
   | `DJANGO_DB_PASSWORD` | `[Your Supabase Password]` |
   | `DJANGO_DB_PORT` | `5432` |
   | `FITME_BRIDGE_TOKEN` | `[Your Bridge Secret Token]` |
   | `LIVEU_API_URL` | `https://attapi.liveucloud.com/api/v1` |
   | `LIVEU_BRANCH_API_KEY` | `[Your LiveU API Key]` |
6. Click **Create Web Service**. Render will build and deploy your portal.

---

### Step 3: Prevent Render Free Tier Sleep (100% Free Keep-Alive)

Free web services on Render spin down after 15 minutes of inactivity. To keep your gym portal **active 24/7 with zero lag**:

1. Go to **[cron-job.org](https://cron-job.org)** and create a free account.
2. Click **Create Cronjob**:
   - **Title:** `Fit Me Portal Keep-Alive`
   - **URL:** `https://your-backend.onrender.com/dashboard/`
   - **Schedule:** Every **10 minutes**
3. Save the job. This guarantees the backend never goes to sleep and stays ready for instant member check-ins.

---

### Step 4: Deploy Next.js Frontend to Vercel

1. Go to **[vercel.com](https://vercel.com)** and log in with GitHub.
2. Click **Add New** ➔ **Project** ➔ Import `sewwas/fitme`.
3. In the project setup screen:
   - **Root Directory:** Click **Edit** and select `fitme-ui`.
   - **Framework Preset:** `Next.js` (auto-detected).
4. Under **Environment Variables**, add:
   ```ini
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```
5. Click **Deploy**. Vercel will build and deploy the frontend in under 60 seconds.
6. Connect your custom domain `fitmefitness.lk` under **Project Settings ➔ Domains**.

---

### Step 5: Initialize Seed Data in Production

Once Render finishes deploying, open the Render **Shell** tab or run locally pointing to the Supabase database:
```bash
python manage.py createsuperuser
```
Create your primary Super Admin user. Then log in to `/dashboard/admin/` to manage plans, staff, and biometric devices.

---

## 🏢 Alternative: On-Premises Gym Mini-PC (Zero Cloud Cost + Local LAN Access)

If you prefer to run the server on a computer inside the gym (e.g. reception desktop or a small $100 Intel N100 mini-PC):

### Benefits:
- **Direct LAN Communication:** Connects straight to the ZKTeco Turnstile Controller at `192.168.1.23` with no external dependencies.
- **Offline Resilience:** Turnstile access continues working even if the gym's fiber/internet connection temporarily drops.
- **Cloudflare Tunnel (`cloudflared`):** Provides a public secure domain (e.g. `https://portal.fitmefitness.lk`) without port forwarding or static IP.

### Quick Setup:
1. Install [Docker Desktop](https://www.docker.com/) on the gym PC.
2. Run:
   ```bash
   docker compose up -d
   ```
3. Install **Cloudflare Tunnel**:
   ```bash
   winget install Cloudflare.cloudflared
   cloudflared tunnel --url http://localhost:8000
   ```
4. Connect the tunnel to your domain in the Cloudflare Zero Trust dashboard.

---

## 🔒 Security Checklist for Production

- [x] `DJANGO_DEBUG=False` in environment variables.
- [x] Unique `SECRET_KEY` generated in production.
- [x] Valid SSL certificates enforced via HTTPS (handled automatically by Vercel and Render).
- [x] Database password stored safely in environment variables (never committed to git).
- [x] Turnstile hardware secured with `FITME_BRIDGE_TOKEN` and LiveU API key.
