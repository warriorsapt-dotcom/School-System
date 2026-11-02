# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **Django school management platform** with a plain HTML/CSS/JS frontend. The project is fully scaffolded and running — Django serves both the REST API and the frontend HTML pages.

**Dev server:** `http://127.0.0.1:8000/`  
**Admin panel:** `http://127.0.0.1:8000/admin/`  
**Default superuser:** `admin@school.com` / `qazwsx123!`

## Setup

```powershell
# Activate the virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Copy and configure environment
copy .env.example .env   # then edit DB_PASSWORD etc.

# Create the database (first time only)
$env:PGPASSWORD="<pg_password>"; psql -U postgres -c "CREATE DATABASE school_platform;"

# Apply migrations and start
python manage.py migrate
python manage.py runserver
```

## Common Commands

All commands must be run from `D:\Users\Benson\Project` with the venv active.

```powershell
python manage.py runserver                           # Dev server
python manage.py migrate                             # Apply migrations
python manage.py makemigrations <app>                # Create migrations
python manage.py test                                # Run all tests
python manage.py test <app>.<TestClass>.<method>     # Run single test
python manage.py shell                               # Django shell
python manage.py createsuperuser                     # Create admin account
python manage.py seed_data                           # Seed realistic test data
python manage.py seed_data --clear                   # Wipe seeded data then re-seed
python manage.py generate_term_results --term first --class "Form 1A"
```

## Project Structure

```
Project/
├── school_platform/        # Django project package (settings, urls, wsgi)
├── users/                  # CustomUser, Teacher, Student, Admin, SchoolImage
│   └── management/commands/seed_data.py   # seed command
├── classes/                # Class, Subject, ClassSubject, Term
│   └── tests.py            # APITestCase suite for class performance endpoint
├── attendance/             # Attendance, AttendanceSummary
├── scores/                 # Score, ScoreComment, SubjectPerformance,
│   │                       #   TermResult, YearlyResult, ProgressLog
│   ├── utils.py            # AcademicCalculations, ResultCalculation, AttendanceUtils
│   └── management/commands/generate_term_results.py
├── templates/frontend/     # login.html, dashboard.html (served by Django TemplateView)
├── static/frontend/        # css/style.css, js/api.js, js/app.js
├── venv/                   # Python 3.14 virtual environment
├── .env                    # DB credentials, secret key (not committed)
└── manage.py
```

The template source files at the project root (`users_models.py`, `views_example.py`, etc.) are the **original delivery package** — the live code is in the app directories above.

## Architecture

### Data Model

Three-layer hierarchy: **Users → Academic Structure → Performance Data**

- **Users**: `CustomUser` (email-based auth, UUID PK) with OneToOne profiles — `Teacher`, `Student`, `Admin`
- **Academic structure**: `Class` → `Subject` → `ClassSubject` (teacher-subject-class assignment), `Term`
- **Performance**: `Score` → `SubjectPerformance` → `TermResult` → `YearlyResult`, plus `ProgressLog` for trends
- **Attendance**: `Attendance` (daily records) → `AttendanceSummary` (pre-aggregated)

### API

REST API at `/api/v1/`. JWT auth (1hr access, 7-day refresh, auto-rotation via `token_blacklist`). Role-based permissions: Admin / Teacher / Student. Pagination: 20 items/page.

Key endpoint groups: `auth/`, `users/teachers/`, `users/students/`, `classes/`, `subjects/`, `terms/`, `attendance/`, `scores/`, `results/`, `images/`, `progress/chart/`

**Custom actions:**
- `GET /api/v1/classes/{id}/student_performance/` — class teacher or admin only; returns per-student scores, attendance, grade, position. Uses 3 bulk queries (no N+1).
- `GET /api/v1/users/teachers/me/` — returns the authenticated teacher's profile plus `my_class` (the class they are assigned to as class teacher, or `null`).

### Role-based data scoping

- **Students** — `AttendanceViewSet.get_queryset()` filters to only that student's own records. Same for scores.
- **Teachers** — `StudentViewSet.get_queryset()` filters to students in classes where the teacher has at least one `ClassSubject` teaching assignment (`teacher.teaching_assignments.values_list('class_obj_id', flat=True)`). Teachers cannot see students outside their classes.
- **Admins** — no filtering; full access to all records.

### Frontend

Plain HTML/CSS/JS single-page app served directly by Django via `TemplateView`.

- **`/`** → `templates/frontend/login.html` — login form, stores JWT in `localStorage`
- **`/dashboard/`** → `templates/frontend/dashboard.html` — SPA shell; all sections rendered by `app.js`
- **`static/frontend/js/api.js`** — API client with auto token-refresh on 401
- **`static/frontend/js/app.js`** — navigation router, section renderers
- **`static/frontend/css/style.css`** — custom styles on top of Bootstrap 5 (CDN)

Nav items and visible sections are filtered by role at runtime via the `NAV` map in `app.js`:

| Role | Sections |
|---|---|
| admin | Dashboard, Students, Teachers, Classes, Subjects, Attendance, Scores, Results, School Images, Profile |
| teacher | Dashboard, Class Performance, My Students, My Classes, Attendance, Scores, Profile |
| student | Dashboard, My Attendance, My Scores, My Results, Profile |

**Key `app.js` functions:**
- `renderClassPerformance()` — teacher-only; calls `teacherMe()` then `classStudentPerformance()`, displays per-student table + charts
- `renderTeacherStudents()` — teacher path for the Students section; groups students by class with a "View Details" button per student
- `openStudentDetail(studentId, studentName)` — modal with parallel fetch of scores + attendance + progress; renders subject bar chart, attendance donut, progress line chart, recent scores table
- `openStudentProgress(studentId, studentName)` — lightweight modal with just the progress line chart (used in admin student list)
- `destroyChart(id)` — always call before `new Chart(...)` to avoid "Canvas already in use" errors

### Chart.js rules

- Always call `destroyChart(id)` before creating a new `Chart` instance on the same canvas ID.
- Chart containers must use `position:relative; height:Xpx` (not `d-flex` / `min-height`).
- All charts must set `maintainAspectRatio: false`.

### Business Logic

Result generation is **not real-time** — run via the `generate_term_results` management command or Celery. `scores/utils.py` contains `AcademicCalculations`, `ResultCalculation`, and `AttendanceUtils`.

Grade scale: A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, E ≥ 50, F < 50.

`AttendanceSummary` records are **not populated by seed data** — never read from `AttendanceSummary` for student-facing views; use raw `Attendance` records instead.

## Key Conventions

- All models use **UUID primary keys**
- **Email** is `USERNAME_FIELD` (not username)
- All models carry `created_at` / `updated_at` timestamps
- Scoring fields use `Decimal`, not `float`
- ForeignKeys use descriptive `related_name` values
- Default timezone: `Africa/Nairobi`
- Frontend auth state lives entirely in `localStorage` (`sp_token`, `sp_refresh`, `sp_user`)
- Static files served at `/static/`, media at `/media/` — both only in `DEBUG=True`
- Windows cp1252 encoding — management command stdout must use ASCII only (no special chars)
- Do **not** use `IsTeacher() | IsAdmin()` as a combined DRF permission — Python 3.14 breaks the `|` operator on permission classes. Use a combined class like `IsTeacherOrAdmin` instead.
- `res.data` from DRF test client returns Python UUID objects, not strings — wrap in `str()` when comparing in tests

## Seed Data

`python manage.py seed_data` creates:
- 8 subjects (5 compulsory, 3 optional)
- 5 classes (Form 1A/1B, Form 2A/2B, Form 3A)
- 7 teachers (`teacher01@school.com` … `teacher07@school.com`, password `school123`)
- 1 term (first term, current year)
- 20 students (`student01@school.com` … `student20@school.com`, password `school123`)
- 30 days of attendance records and scores for all assessment types

The first 5 teachers are automatically assigned as class teachers (one per class) and the corresponding `Class.class_teacher` FK is set.

## Security Notes

**JWT in localStorage**: Tokens are stored in `localStorage`, which is accessible to JavaScript and therefore vulnerable to XSS. For production, consider migrating to `httpOnly` cookies. The current approach is acceptable for internal/school use.

**Rate limiting**: Login endpoint is throttled at 5 requests/minute (`LoginRateThrottle`). Global API rates: anonymous 100/hour, authenticated 1000/hour. Adjust in `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']` in `settings.py`.

## Celery (Async Tasks)

Celery is configured but requires Redis to be running. To start a Celery worker:

```powershell
# Requires Redis running on localhost:6379
celery -A school_platform worker --loglevel=info
```

The `generate_term_results_async` task in `scores/tasks.py` wraps the management command. Trigger via Django shell: `from scores.tasks import generate_term_results_async; generate_term_results_async.delay()`.
