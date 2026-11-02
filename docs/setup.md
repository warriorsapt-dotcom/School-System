# Setup Guide

All commands run from `D:\Users\Benson\Project` with the virtual environment active.

## Prerequisites

- **Python 3.14** (the bundled `venv/` targets this version)
- **PostgreSQL** running locally on port `5432`
- **Redis** (optional — only needed for Celery async tasks)

## 1. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

If you need to recreate dependencies:

```powershell
pip install -r requirements.txt
```

`requirements.txt` pins: Django 4.2.11, DRF 3.14, django-cors-headers, psycopg2-binary,
python-decouple, djangorestframework-simplejwt 5.5.1, Pillow, django-filter 23.5,
celery, redis, matplotlib.

## 2. Configure environment variables

Copy the example file and edit the secrets:

```powershell
copy .env.example .env
```

Settings are read by `python-decouple`. Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `DEBUG` | `True` | Debug mode. Static/media are only served when `True`. |
| `SECRET_KEY` | insecure default | Django secret. Also used as the JWT signing key. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts. |
| `DB_NAME` | `school_platform` | PostgreSQL database name. |
| `DB_USER` | `postgres` | Database user. |
| `DB_PASSWORD` | `postgres` | Database password — **set this**. |
| `DB_HOST` | `localhost` | Database host. |
| `DB_PORT` | `5432` | Database port. |
| `CORS_ALLOWED_ORIGINS` | `localhost:3000,...` | Comma-separated CORS origins. |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker + result backend. |
| `EMAIL_*` | console backend | SMTP settings (dev uses the console backend). |

## 3. Create the database (first time only)

```powershell
$env:PGPASSWORD="<pg_password>"; psql -U postgres -c "CREATE DATABASE school_platform;"
```

## 4. Apply migrations

```powershell
python manage.py migrate
```

## 5. (Optional) Seed realistic test data

```powershell
python manage.py seed_data            # create seed data
python manage.py seed_data --clear    # wipe seeded data then re-seed
```

This creates:

- 8 subjects (5 compulsory, 3 optional)
- 5 classes (Form 1A/1B, Form 2A/2B, Form 3A)
- 7 teachers — `teacher01@school.com` … `teacher07@school.com`, password `school123`
- 1 term (first term, current year)
- 20 students — `student01@school.com` … `student20@school.com`, password `school123`
- 30 days of attendance records and scores for all assessment types

The first 5 teachers are assigned as class teachers (one per class), setting each
`Class.class_teacher`.

> **Note:** `AttendanceSummary` rows are **not** populated by seed data. Student-facing
> views read raw `Attendance` records instead.

## 6. Run the development server

```powershell
python manage.py runserver
```

- Frontend login: http://127.0.0.1:8000/
- Dashboard (after login): http://127.0.0.1:8000/dashboard/
- Django admin: http://127.0.0.1:8000/admin/  (`admin@school.com` / `qazwsx123!`)

## Common management commands

```powershell
python manage.py runserver                           # Dev server
python manage.py migrate                             # Apply migrations
python manage.py makemigrations <app>                # Create migrations
python manage.py test                                # Run all tests
python manage.py test <app>.<TestClass>.<method>     # Run a single test
python manage.py shell                               # Django shell
python manage.py createsuperuser                     # Create an admin account
python manage.py seed_data                           # Seed test data
python manage.py generate_term_results --term first --class "Form 1A"
```

## Generating term results

Result records are **not** computed in real time. Generate them with:

```powershell
python manage.py generate_term_results --term first --class "Form 1A"
```

Or asynchronously via Celery (requires Redis on `localhost:6379`):

```powershell
celery -A school_platform worker --loglevel=info
```

```python
# In python manage.py shell
from scores.tasks import generate_term_results_async
generate_term_results_async.delay()
```

## Windows encoding note

The Windows console uses cp1252. Management-command stdout must be **ASCII only**
(no special characters), or output will fail to encode.
