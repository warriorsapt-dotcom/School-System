# API Reference

Base URL: **`/api/v1/`** (e.g. `http://127.0.0.1:8000/api/v1/`)

- **Auth:** JWT bearer token. Send `Authorization: Bearer <access_token>` on every
  request except the public auth endpoints.
- **Default permission:** `IsAuthenticated` (all endpoints require login unless noted).
- **Pagination:** page-number, 20 items per page. Responses are wrapped as
  `{ "count", "next", "previous", "results": [...] }`.
- **Filtering:** most list endpoints support `DjangoFilterBackend` filters, `search`, and
  `ordering` query parameters.
- **Throttling:** anonymous `100/hour`, authenticated `1000/hour`, login `5/minute`.

## Authentication

### `POST /api/v1/auth/login/` — *public*

Throttled at 5/minute.

```json
// Request
{ "email": "admin@school.com", "password": "qazwsx123!" }

// 200 OK
{ "access": "<jwt>", "refresh": "<jwt>", "user": { ...CustomUser... } }
// 401 if credentials are invalid
```

### `POST /api/v1/auth/register/` — *public*

Creates a user and returns tokens (`201`).

```json
{ "access": "<jwt>", "refresh": "<jwt>", "user": { ... } }
```

### `POST /api/v1/auth/logout/` — *authenticated*

Blacklists the supplied refresh token.

```json
// Request
{ "refresh_token": "<jwt>" }
// 200 { "detail": "Successfully logged out" }
```

### `POST /api/v1/auth/change-password/` — *authenticated*

```json
{ "old_password": "...", "new_password": "..." }
// 200 on success, 400 if old password is wrong
```

### `GET|PUT /api/v1/auth/profile/` — *authenticated*

`GET` returns the current user; `PUT` partially updates it.

### SimpleJWT token endpoints

- `POST /api/v1/auth/token/` — obtain a token pair (`email` + `password`).
- `POST /api/v1/auth/token/refresh/` — exchange a refresh token for a new access token.

---

## Users

### Teachers — `/api/v1/users/teachers/`

ModelViewSet. `create` and `destroy` require **admin**; other actions require any
authenticated user.

- Filters: `is_class_teacher`, `is_active`
- Search: first name, last name, `employee_id`
- Ordering: first name, `hire_date`

| Method | Path | Notes |
|---|---|---|
| GET | `/users/teachers/` | List teachers |
| POST | `/users/teachers/` | Create (admin) |
| GET | `/users/teachers/{id}/` | Retrieve |
| PUT/PATCH | `/users/teachers/{id}/` | Update |
| DELETE | `/users/teachers/{id}/` | Delete (admin) |
| GET | `/users/teachers/me/` | The authenticated teacher's profile plus `my_class` (their class-teacher class, or `null`). `404` if the user is not a teacher. |
| GET | `/users/teachers/{id}/classes/` | Classes this teacher is class teacher of |
| GET | `/users/teachers/{id}/subjects/` | This teacher's `ClassSubject` assignments |

### Students — `/api/v1/users/students/`

ModelViewSet. `create` and `destroy` require **admin**.

**Scoping:** teachers see only students in classes they have a `ClassSubject` assignment
in; students/admins per default rules.

- Filters: `class_assigned`, `is_active`
- Search: first name, last name, `admission_number`
- Ordering: first name, `admission_date`

| Method | Path | Notes |
|---|---|---|
| GET | `/users/students/` | List (scoped for teachers) |
| POST | `/users/students/` | Create (admin) |
| GET | `/users/students/{id}/` | Retrieve |
| PUT/PATCH | `/users/students/{id}/` | Update |
| DELETE | `/users/students/{id}/` | Delete (admin) |
| GET | `/users/students/{id}/results/` | Term results; optional `?term=<id>` |
| GET | `/users/students/{id}/progress/` | Progress logs, oldest first |

### School images — `/api/v1/images/`

ModelViewSet, only `is_published=True` rows. `create`/`update`/`partial_update`/`destroy`
require **admin**. On create, `uploaded_by` is set to the current user.

- Filters: `category`, `is_published`
- Search: `title`, `description`

---

## Classes

### Classes — `/api/v1/classes/`

ModelViewSet. Write actions (`create`/`update`/`partial_update`/`destroy`) require
**admin**. `retrieve` uses a detailed serializer.

- Filters: `form_level`, `is_active`
- Search: `name`, `stream`
- Ordering: `form_level`, `section`

| Method | Path | Notes |
|---|---|---|
| GET | `/classes/` | List classes |
| GET | `/classes/{id}/` | Retrieve (detail serializer) |
| POST/PUT/PATCH/DELETE | `/classes/{id}/` | Admin only |
| GET | `/classes/{id}/attendance/` | All attendance records for the class |
| GET | `/classes/{id}/student_performance/` | **Class teacher of this class or admin only.** Per-student scores, attendance, grade, position. See below. |

#### `GET /classes/{id}/student_performance/`

Returns aggregated performance for the class using the current term (`Term.is_current`).
Computed with three bulk queries (scores, term results, attendance) to avoid N+1. Returns
`403` if the requester is neither admin nor this class's class teacher.

```json
{
  "class_name": "Form 1A",
  "form_level": 1,
  "section": "A",
  "total_students": 4,
  "current_term": "First Term 2024/2025",
  "all_subjects": ["English", "Mathematics", "..."],
  "students": [
    {
      "student_id": "<uuid>",
      "student_name": "Jane Doe",
      "admission_number": "ADM001",
      "average_percentage": 78.5,
      "overall_grade": "C",
      "position_in_class": 1,
      "subjects_passed": 6,
      "subjects_failed": 1,
      "status": "promoted",
      "attendance_rate": 96.7,
      "attendance_present": 29,
      "attendance_total": 30,
      "subjects": { "Mathematics": 82.0, "English": 75.0 }
    }
  ]
}
```

Students are sorted by `position_in_class` (then descending average). When a `TermResult`
exists it is preferred for the average/grade/position; otherwise values are derived from
raw scores and grade/position fall back to `—` / `null`.

### Subjects — `/api/v1/subjects/`

ModelViewSet. Search: `name`, `code`. Ordering: `name`.

### Terms — `/api/v1/terms/`

**Read-only** ViewSet. Filters: `academic_year`, `is_current`.

---

## Attendance — `/api/v1/attendance/`

ModelViewSet. Write actions and `bulk_mark` require **teacher or admin**. Students see only
their own records. On create, `teacher` is set from the requester's `teacher_profile`.

- Filters: `student`, `class_obj`, `date`, `status`, `term`
- Search: student first/last name
- Ordering: `date`

| Method | Path | Notes |
|---|---|---|
| GET | `/attendance/` | List (scoped for students) |
| POST | `/attendance/` | Create (teacher/admin) |
| GET/PUT/PATCH/DELETE | `/attendance/{id}/` | Detail / write (teacher/admin) |
| GET | `/attendance/summary/` | `AttendanceSummary` rows; optional `?student=`, `?class=`, `?term=`. Students scoped to self. |
| POST | `/attendance/bulk_mark/` | Bulk create. Body: `{ "attendances": [ {...}, ... ] }`. Returns `{ "created": [...] }`. |

> `AttendanceSummary` is not populated by seed data; `summary/` returns empty unless you
> generate summaries.

---

## Scores — `/api/v1/scores/`

ModelViewSet. Write actions require **teacher or admin**. Students see only their own
scores. `retrieve` uses a detailed serializer.

- Filters: `student`, `subject`, `term`, `assessment_type`
- Search: student first name, subject name
- Ordering: `-date_recorded`, `percentage`

| Method | Path | Notes |
|---|---|---|
| GET | `/scores/` | List (scoped for students) |
| POST | `/scores/` | Create (teacher/admin) |
| GET/PUT/PATCH/DELETE | `/scores/{id}/` | Detail / write (teacher/admin) |
| POST | `/scores/{id}/add_comment/` | Add a `ScoreComment`; `teacher` set from requester. |
| GET | `/scores/student_scores/?student=<id>` | All scores for one student. `400` if `student` missing. |

`percentage` is computed automatically from `marks_obtained` / `max_marks`.

---

## Results — `/api/v1/results/`

**Read-only** ViewSet over `TermResult`. Students see only their own results.

- Filters: `student`, `term`, `class_obj`, `status`

| Method | Path | Notes |
|---|---|---|
| GET | `/results/` | List term results (scoped for students) |
| GET | `/results/{id}/` | Retrieve |
| GET | `/results/class_ranking/?class=<id>&term=<id>` | Results ordered by `position_in_class`. Both params required (`400` otherwise). |
| GET | `/results/export_csv/` | Streams the filtered results as `term_results.csv`. |

---

## Progress chart — `/api/v1/progress/chart/`

`GET /api/v1/progress/chart/?student=<id>` — returns Chart.js-ready data built from the
student's `ProgressLog` rows (oldest first). `400` if `student` is missing, `404` if the
student does not exist.

```json
{
  "labels": ["First Term", "Second Term"],
  "datasets": [{
    "label": "Average Percentage",
    "data": [72.0, 78.5],
    "borderColor": "rgb(75, 192, 192)",
    "backgroundColor": "rgba(75, 192, 192, 0.2)"
  }]
}
```

---

## Browsable API

DRF's browsable API and session login are mounted at `/api-auth/` when developing.
