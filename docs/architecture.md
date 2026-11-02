# Architecture

## Overview

Django serves both the REST API (`/api/v1/`) and the frontend HTML pages. The frontend
is a plain HTML/CSS/JS single-page app that talks to the API using a JWT stored in
`localStorage`.

```
Browser (HTML/JS SPA)  ──JWT──>  Django REST API (/api/v1/)  ──>  PostgreSQL
        ▲                                  │
        └──── TemplateView (login, dashboard) ───┘
```

## Data model

Three layers: **Users → Academic structure → Performance data**.

### Users (`users` app)

- **`CustomUser`** — email-based auth, UUID primary key. `USERNAME_FIELD = 'email'`.
  Roles: `admin`, `principal`, `teacher`, `student`. Carries `phone_number`,
  `profile_picture`, `is_active`, `created_at`/`updated_at`.
- **`Teacher`** — OneToOne with `CustomUser` (`related_name='teacher_profile'`).
  `employee_id`, `qualification`, `subject_specialization`, `is_class_teacher`.
- **`Student`** — OneToOne with `CustomUser` (`related_name='student_profile'`).
  `admission_number`, `class_assigned` (FK → `Class`, `related_name='students'`),
  parent info, `get_age()` helper.
- **`Admin`** — OneToOne with `CustomUser` (`related_name='admin_profile'`).
- **`SchoolImage`** — gallery images with `category`, `is_published`, `uploaded_by`.

### Academic structure (`classes` app)

- **`Class`** — `name` (unique per year), `class_teacher` (FK → `Teacher`,
  `related_name='classes_teaching'`), `form_level` (1–6), `section`, `stream`,
  `capacity`, `year`. `get_student_count()` helper. Unique on `(name, year)`.
- **`Subject`** — `name`, `code`, `is_compulsory`.
- **`ClassSubject`** — links a `Class` + `Subject` + `Teacher` for an `academic_year`.
  Teacher `related_name='teaching_assignments'`. Unique on
  `(class_obj, subject, academic_year)`. **This is the join model that defines what a
  teacher teaches and where.**
- **`Term`** — `first`/`second`/`third`, `academic_year`, dates, `is_current`.
  Unique on `(name, academic_year)`.

### Attendance (`attendance` app)

- **`Attendance`** — one record per `(student, date, class_obj)`. `status` is one of
  `present`, `absent`, `late`, `excused`, `medical`. Indexed on `date`, `student`,
  `class_obj`.
- **`AttendanceSummary`** — pre-aggregated per `(student, class_obj, term)` with
  `calculate_attendance_percentage()`. **Not populated by seed data** — do not read it
  for student-facing views; aggregate raw `Attendance` instead.

### Performance (`scores` app)

- **`Score`** — a single assessment result. `assessment_type` ∈ `test`, `exam`,
  `assignment`, `project`, `class_work`, `homework`. `percentage` is auto-computed in
  `save()` as `marks_obtained / max_marks * 100`. `get_grade()` applies the grade scale.
- **`ScoreComment`** — teacher comment on a score (`positive`/`constructive`/`neutral`).
- **`SubjectPerformance`** — aggregated per `(student, subject, term)`: average %, grade,
  `rank_in_class`.
- **`TermResult`** — aggregated per `(student, term, class_obj)`: totals, `average_percentage`,
  `position_in_class`, `overall_grade`, subjects passed/failed, best/worst subject,
  `status` (`promoted`/`retained`/`conditional`/`pending`), approval fields.
- **`YearlyResult`** — links three `TermResult`s for a year, `annual_average`,
  `improvement_trend`.
- **`ProgressLog`** — per-term trend snapshot: `average_percentage`, `rank_in_class`,
  `improvement_flag` (`high`/`average`/`at_risk`). Drives the progress chart.

### Grade scale

| Grade | Percentage |
|---|---|
| A | ≥ 90 |
| B | ≥ 80 |
| C | ≥ 70 |
| D | ≥ 60 |
| E | ≥ 50 |
| F | < 50 |

## Authentication

- JWT via `djangorestframework-simplejwt`.
- **Access token:** 1 hour. **Refresh token:** 7 days.
- `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True` — old refresh
  tokens are blacklisted on rotation (`token_blacklist` app).
- Signing key is the Django `SECRET_KEY`, algorithm `HS256`.

## Role-based data scoping

Enforced in each ViewSet's `get_queryset()` / `get_permissions()`:

- **Students** — see only their own records. `AttendanceViewSet`, `ScoreViewSet`, and
  `TermResultViewSet` filter `student__user == request.user`.
- **Teachers** — `StudentViewSet.get_queryset()` filters to students in classes where the
  teacher has at least one `ClassSubject` assignment
  (`teacher.teaching_assignments.values_list('class_obj_id', flat=True)`). Teachers cannot
  see students outside their classes.
- **Admins** — no filtering; full access.

Custom permission classes live in `users/views.py`: `IsAdmin`, `IsTeacher`,
`IsTeacherOrAdmin`, `IsOwnerOrAdmin`.

> **Python 3.14 caveat:** do **not** combine permissions with the `|` operator
> (`IsTeacher() | IsAdmin()`) — it breaks. Use a combined class like `IsTeacherOrAdmin`.

## Frontend

Plain HTML/CSS/JS SPA served by Django `TemplateView`:

- **`/`** → `templates/frontend/login.html` — login form, stores JWT in `localStorage`.
- **`/dashboard/`** → `templates/frontend/dashboard.html` — SPA shell; sections rendered
  by `app.js`.
- **`static/frontend/js/api.js`** — API client with automatic token refresh on `401`.
- **`static/frontend/js/app.js`** — navigation router and section renderers.
- **`static/frontend/css/style.css`** — custom styles over Bootstrap 5 (CDN).

Auth state lives entirely in `localStorage`: `sp_token`, `sp_refresh`, `sp_user`.

### Navigation by role (the `NAV` map in `app.js`)

| Role | Sections |
|---|---|
| admin | Dashboard, Students, Teachers, Classes, Subjects, Attendance, Scores, Results, School Images, Profile |
| teacher | Dashboard, Class Performance, My Students, My Classes, Attendance, Scores, Profile |
| student | Dashboard, My Attendance, My Scores, My Results, Profile |

### Chart.js rules

- Call `destroyChart(id)` before creating a new `Chart` on the same canvas ID (avoids
  "Canvas already in use").
- Chart containers use `position:relative; height:Xpx` (not `d-flex` / `min-height`).
- All charts set `maintainAspectRatio: false`.

## Business logic

Result generation is **not real-time** — run via the `generate_term_results` management
command or the `generate_term_results_async` Celery task. The math lives in
`scores/utils.py`: `AcademicCalculations`, `ResultCalculation`, `AttendanceUtils`.

## Key conventions

- All models use **UUID primary keys**.
- **Email** is the username field (not `username`).
- All models carry `created_at` / `updated_at`.
- Scoring fields use `Decimal`, not `float`.
- ForeignKeys use descriptive `related_name`s.
- Default timezone: `Africa/Nairobi`.
- Static at `/static/`, media at `/media/` — both served only when `DEBUG=True`.
- Management-command stdout must be ASCII only (Windows cp1252).
- In DRF tests, `res.data` returns Python `UUID` objects — wrap in `str()` when comparing.
