# TimeTrack — Multi-Client Time Tracking for Consulting / BPO Firms

Track how many hours each employee works for each client, every day —
with support for **dedicated** resources (one client) and **shared**
resources (split across many clients), plus teams, team leaders, project
managers and project heads.

This repository is **Iteration 1: the foundation** — the project skeleton,
the full data model, login/sign-up, and a working time-logging API.
Client/project/allocation APIs and reporting are added in later iterations.

## Tech stack
- **Django + Django REST Framework** (API)
- **PostgreSQL** in production (SQLite auto-used for first local run)
- **JWT** authentication (login returns access + refresh tokens)
- **Redis + Celery** wired in for future background reports/notifications

## The data model (in one breath)
An **Organization** (the firm) has **Users** (with a role: Owner, Admin,
Project Head, Project Manager, Team Leader, Employee). The firm serves
**Clients**, each Client has **Projects**. An **Allocation** connects a
User to a Project (and therefore a Client) and marks them DEDICATED or
SHARED. A **TimeEntry** records hours a User logged on a Project/Client on
a given day; entries roll up into a **Timesheet** for approval.

## Run it locally (5 steps)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then set a long random SECRET_KEY
python manage.py migrate      # uses SQLite because DATABASE_URL is blank
python manage.py createsuperuser
python manage.py runserver
```
Then open http://127.0.0.1:8000/admin/ to manage data, or call the API.

## API available in this iteration
| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/auth/register-org/ | Sign up a new firm + owner |
| POST | /api/auth/login/ | Log in, returns JWT tokens |
| POST | /api/auth/token/refresh/ | Refresh an expired access token |
| GET  | /api/auth/me/ | Current user's profile |
| GET/POST | /api/users/ | List / add employees (managers) |
| PATCH/DELETE | /api/users/{id}/ | Edit / deactivate an employee |
| GET/POST | /api/clients/ | List / create clients (managers create) |
| GET/PATCH/DELETE | /api/clients/{id}/ | One client |
| GET/POST | /api/projects/ | List / create projects (managers create) |
| GET/PATCH/DELETE | /api/projects/{id}/ | One project |
| GET/POST | /api/allocations/ | Assign employees (dedicated/shared) |
| GET/PATCH/DELETE | /api/allocations/{id}/ | One allocation |
| GET | /api/allocations/matrix/ | Employee x client grid (managers) |
| GET | /api/reports/hours-by-client/ | Hours per client (managers) |
| GET | /api/reports/hours-by-employee/ | Hours per employee (managers) |
| GET | /api/reports/hours-by-project/ | Hours per project (managers) |
| GET | /api/reports/utilization/ | Worked vs capacity per employee (managers) |
| GET | /api/reports/billing-export/ | Per-client revenue, cost & margin (managers) |
| GET/POST | /api/time-entries/ | List / create time entries |
| GET/PATCH/DELETE | /api/time-entries/{id}/ | One time entry |
| GET | /api/timer/active/ | The user's running timer (if any) |
| POST | /api/timer/start/ | Start a timer on a project |
| POST | /api/timer/stop/ | Stop & roll the session into the day's hours |
| POST | /api/agent/heartbeat/ | Desktop agent reports activity + active minutes |

Time-entry list filters: `?client= ?project= ?user= ?date_from= ?date_to= ?status=`

## Going to production (later)
- Set `DEBUG=False`, a long `SECRET_KEY`, real `ALLOWED_HOSTS`.
- Set `DATABASE_URL` to PostgreSQL.
- Serve with Gunicorn behind Nginx; run Celery workers against Redis.


Client filters: `?status= ?search=`  |  Project filters: `?client= ?status= ?search=`

Allocation filters: `?user= ?project= ?client= ?type=DEDICATED|SHARED ?active=true|false`

Allocation rules enforced automatically: a dedicated employee serves one client only; total active allocation per employee never exceeds 100%.

Report filters: `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` (defaults to the current month). Utilization assumes an 8-hour weekday capacity.

Billing uses a **rate snapshot**: each time entry freezes the employee's bill/cost rate when logged, so later rate changes never alter past invoices. Hours logged with no rate set are reported as `unrated_hours`.
