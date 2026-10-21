# NagorikFix API

Public infrastructure reporting backend (Django + DRF).

## Core flow

```
Nagorik login
  → fill form (category, union, ward, description, max 3 photos)
  → submit report (status: pending)

Administration (same district)
  → see inbox
  → assign a Staff member (status: assigned)

Staff
  → see assigned tasks
  → mark in_progress / resolved
```

---

## Actors & auth

| Role | Signup | Login |
| --- | --- | --- |
| **nagorik** | approved immediately | phone + password |
| **staff** | pending until approved | phone + password |
| **administration** | pending until approved | phone + password |

- Unique id: **phone**
- Each user → **one district**
- `POST /api/auth/approve/{user_id}/` for staff/admin approval

---

## Report APIs

### Nagorik

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/categories/` | Form dropdown |
| POST | `/api/reports/` | multipart submit |
| GET | `/api/reports/` | Own reports |
| GET | `/api/reports/{id}/` | Own report detail |

**Submit body** (`multipart/form-data`):

| Field | Required |
| --- | --- |
| `category_id` | yes |
| `union` | yes |
| `ward` | yes |
| `description` | yes (≥ 10 chars) |
| `photos` | optional, max **3** images (repeat field) |
| `latitude` / `longitude` | optional |

District is taken from the Nagorik profile automatically.

### Administration

| Method | Path |
| --- | --- |
| GET | `/api/admin/reports/` (`?status=pending`) |
| GET | `/api/admin/reports/{id}/` |
| GET | `/api/admin/staff/` |
| POST | `/api/admin/reports/{id}/assign/` `{ "staff_id": 5 }` |
| PATCH | `/api/admin/reports/{id}/priority/` `{ "priority": "high" }` |
| POST | `/api/admin/reports/{id}/reject/` |
| GET | `/api/admin/dashboard/stats/` |

### Staff

| Method | Path |
| --- | --- |
| GET | `/api/staff/tasks/` |
| GET | `/api/staff/tasks/{id}/` |
| PATCH | `/api/staff/tasks/{id}/status/` `{ "status": "in_progress" \| "resolved" }` |

### Status values

`pending` → `assigned` → `in_progress` → `resolved`  
(also `rejected` by administration)

---

## Setup

```bash
cd NagorikFixAPI
source ../venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_districts
python manage.py seed_categories
python manage.py createsuperuser   # phone-based

python manage.py runserver
```

Swagger: http://localhost:8000/api/docs/
