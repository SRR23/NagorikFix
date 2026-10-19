# NagorikFix API

**NagorikFix** — Public Infrastructure Reporting System backend (Django + DRF).

Citizens report issues (roads, drainage, street lights, …). Authority admins triage and assign. Field officers resolve with before/after proof.

---

## Actors

| Role | How they auth | What they do (MVP) |
| --- | --- | --- |
| Citizen | Register / login JWT | Submit report + media, track status |
| Admin (`role=admin`) | Login JWT | Dashboard stats, assign, set priority |
| Field officer | Login JWT | See assigned tasks, upload proof, resolve |
| Django superuser | `/admin/` or JWT | Full Django admin |

Public self-registration always creates `role=citizen`. Create admin/officer accounts via Django admin or `createsuperuser` + role edit.

---

## What is included in this template (MVP)

- Auth: register, login, refresh, logout, me
- Categories (one-click reporting list)
- Reports: create (GPS + optional anonymous), list, detail
- Media upload endpoint
- Admin/officer status / priority / assign update
- Simple dashboard stats
- Docker Compose (web + Postgres + Redis + Celery)
- Swagger at `/api/docs/`

**Not yet:** push notifications, heatmap, SLA escalation, AI duplicate detection, gamification, offline sync. Those come in later phases.

---

## Environment files

| File | When to use |
| --- | --- |
| `.env.example` | Template for local (non-Docker) runs |
| `.env` | Your local secrets — copy from `.env.example` |
| `.env.docker.example` | Template for Docker Compose |
| `.env.docker` | Compose env — copy from `.env.docker.example` |

---

## Setup without Docker

**Requirements:** Python 3.10+, local Postgres.

```bash
cd NagorikFixAPI

# From parent folder you can also use the shared venv:
# source ../venv/bin/activate

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Create DB: createdb nagorikfix

python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser

python manage.py runserver
```

- API: http://localhost:8000  
- Health: http://localhost:8000/api/health/  
- Swagger: http://localhost:8000/api/docs/  

```bash
pytest
```

---

## Setup with Docker

```bash
cd NagorikFixAPI
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up --build
```

Then:

```bash
docker compose --env-file .env.docker exec web python manage.py seed_categories
docker compose --env-file .env.docker exec web python manage.py createsuperuser
```

- API: http://localhost:8001  
- Swagger: http://localhost:8001/api/docs/  

---

## Main API routes

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/auth/register/` | Citizen signup |
| POST | `/api/auth/login/` | Email + password → JWT |
| GET | `/api/auth/me/` | Current user |
| GET | `/api/categories/` | One-click categories |
| POST | `/api/reports/` | Create report (GPS required) |
| GET | `/api/reports/` | List (scoped by role) |
| GET | `/api/reports/{id}/` | Detail + media |
| PATCH | `/api/reports/{id}/update/` | Status / priority / assign |
| POST | `/api/reports/{id}/media/` | Multipart file upload |
| GET | `/api/admin/dashboard/stats/` | Admin aggregates |

---

## Project layout

```
NagorikFixAPI/
  apps/
    accounts/     # User model + JWT auth
    reports/      # Category, Report, ReportMedia
  config/         # Django settings, urls, celery
  utils/          # permissions, constants, exceptions
  docker/         # entrypoint
```
