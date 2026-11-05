# School Management Platform — Documentation

For a fresh VMware installation, follow the [Kahuho VM setup guide](kahuho-vm-setup.md).

A Django-based school management platform with a REST API and a plain HTML/CSS/JS
frontend. Django serves both the `/api/v1/` API and the frontend pages.

- **Dev server:** http://127.0.0.1:8000/
- **Admin panel:** http://127.0.0.1:8000/admin/
- **Default superuser:** `admin@school.com` / `qazwsx123!`

## Documentation index

| Document | What's inside |
|---|---|
| [setup.md](setup.md) | Prerequisites, environment configuration, database, running the server, seeding data |
| [architecture.md](architecture.md) | High-level architecture, data model, role-based scoping, frontend, business logic |
| [api-reference.md](api-reference.md) | Every REST endpoint, auth, permissions, filters, custom actions, examples |
| [user-guide.md](user-guide.md) | How admins, teachers, and students use the web app |

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2, Django REST Framework 3.14 |
| Auth | JWT (`djangorestframework-simplejwt`) with refresh-token rotation + blacklist |
| Database | PostgreSQL (via `psycopg2-binary`) |
| Filtering | `django-filter` |
| Async (optional) | Celery + Redis |
| Frontend | Plain HTML/CSS/JS, Bootstrap 5 (CDN), Chart.js |
| Config | `python-decouple` (`.env` file) |

## Apps at a glance

| App | Responsibility |
|---|---|
| `users` | `CustomUser` (email login, UUID PK), `Teacher`, `Student`, `Admin`, `SchoolImage` |
| `classes` | `Class`, `Subject`, `ClassSubject`, `Term` |
| `attendance` | `Attendance` daily records, `AttendanceSummary` aggregates |
| `scores` | `Score`, `ScoreComment`, `SubjectPerformance`, `TermResult`, `YearlyResult`, `ProgressLog` |
| `school_platform` | Project package — settings, root URLs, WSGI/ASGI, Celery |

## Quick start

```powershell
.\venv\Scripts\Activate.ps1
copy .env.example .env        # then edit DB_PASSWORD etc.
python manage.py migrate
python manage.py seed_data    # optional: realistic test data
python manage.py runserver
```

See [setup.md](setup.md) for the full walkthrough.
