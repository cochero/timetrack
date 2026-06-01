# TimeTrack — Multi-Client Time Tracking for Consulting / BPO Firms

Track how many hours each employee works for each client, every day — with
dedicated and shared resources, teams, approvals, reporting, and billing.

The project has two parts:

- **`backend/`** — Django REST API (the engine). Auth, clients, projects,
  allocations, time tracking, reports, and billing. Fully working and tested.
- **`deploy/`** — production deploy guide (DEPLOY.md), Nginx and systemd config for putting it on a VPS.
- **`agent/`** — an optional Windows desktop agent that auto-logs active time and app/window titles to your server (transparent, no keystrokes/screenshots).
- **`frontend/`** — React + Vite web app (what people see). Iteration 1:
  sign-in, app shell, live dashboard, client/project management, a weekly timesheet, a reports view, people and allocation management, plus a live start/stop work timer. More screens added each iteration.

## Quick start

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # set a long random SECRET_KEY
python manage.py migrate      # uses SQLite until you set DATABASE_URL
python manage.py createsuperuser
python manage.py runserver     # http://localhost:8000
```
Create your firm: `POST http://localhost:8000/api/auth/register-org/` with
`organization_name`, `full_name`, `email`, `password` — or add data through the
admin panel at http://localhost:8000/admin/.

### 2. Frontend
```bash
cd frontend
cp .env.example .env          # VITE_API_BASE_URL=http://localhost:8000/api
npm install
npm run dev                    # http://localhost:5173
```
Sign in with the firm owner you created, and the dashboard will show your
hours-by-client data.

## What works today
People & roles · clients · projects · dedicated/shared allocations (with
guardrails) · daily time logging · reports (hours by client / employee /
project, utilization) · billing export (revenue, cost, margin with rate
snapshots) · web sign-in, dashboard, client/project management, a weekly timesheet, a manager reports view (hours, utilization, billing), employee management, the dedicated/shared allocation matrix, and a one-click quick-start timer (tap a project to start/switch/stop), plus an optional desktop agent for automatic, transparent activity tracking.

## Roadmap
Frontend screens for clients, projects, allocations and time entry · timesheet
approval workflow · scale hardening (caching, read replicas, partitioning) ·
later: desktop monitoring agent, integrations, payroll.
