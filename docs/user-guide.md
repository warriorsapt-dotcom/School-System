# User Guide

This guide describes how the three roles — **Admin**, **Teacher**, and **Student** — use
the web app. The interface adapts automatically to your role: the navigation menu and the
sections you can open are filtered after login.

## Signing in

1. Open http://127.0.0.1:8000/.
2. Enter your **email** and **password** and submit.
3. On success you land on the dashboard (`/dashboard/`). Your session (JWT) is kept in the
   browser; the app refreshes it automatically until the refresh token expires (7 days).
4. Use **Profile → Logout** to sign out (this invalidates your refresh token).

> Default accounts after seeding: admins via the Django superuser
> (`admin@school.com` / `qazwsx123!`), teachers `teacher01..07@school.com` and students
> `student01..20@school.com`, all with password `school123`.

---

## Admin

Admins have full access. Navigation: **Dashboard, Students, Teachers, Classes, Subjects,
Attendance, Scores, Results, School Images, Profile.**

| Task | Where |
|---|---|
| See system overview | **Dashboard** |
| Add / edit / remove students | **Students** (admin can create and delete) |
| Add / edit / remove teachers | **Teachers** |
| Create classes, assign class teachers | **Classes** |
| Manage subjects | **Subjects** |
| View / mark attendance for any class | **Attendance** |
| Enter and edit scores | **Scores** |
| View results, class rankings, export CSV | **Results** |
| Manage gallery images | **School Images** |
| View a student's progress trend | **Students → progress** |

Admins can open any class's performance view and export term results to CSV from the
Results section. Full administrative control (bulk edits, raw records) is also available in
the Django admin at `/admin/`.

---

## Teacher

Navigation: **Dashboard, Class Performance, My Students, My Classes, Attendance, Scores,
Profile.**

Teachers see only the students in the classes they teach (defined by their
`ClassSubject` assignments). A teacher who is also a **class teacher** of a class gets the
class-performance view for that class.

| Task | Where / how |
|---|---|
| See your assigned class & summary | **Class Performance** — loads your class teacher class, then a per-student table with averages, grade, position, attendance, plus charts. |
| Browse your students | **My Students** — students grouped by class, each with a **View Details** button. |
| Inspect one student | **View Details** opens a modal with subject bar chart, attendance donut, progress line chart, and recent scores. |
| See classes you teach | **My Classes** |
| Mark attendance | **Attendance** — create records (single or bulk); your teacher profile is recorded as the marker. |
| Enter scores | **Scores** — create/edit scores; `percentage` is computed for you. Add comments to a score. |

Teachers **cannot** access students or classes outside their assignments — those records
are filtered out by the API.

---

## Student

Navigation: **Dashboard, My Attendance, My Scores, My Results, Profile.**

Students see only their **own** data — the API scopes every list to the logged-in student.

| Task | Where |
|---|---|
| Overview of your performance | **Dashboard** |
| Your attendance history | **My Attendance** |
| Your scores per subject/assessment | **My Scores** |
| Your term results & position | **My Results** |
| Your progress over terms | Progress line chart (built from your progress logs) |
| Update your details / password | **Profile** |

---

## Understanding grades

Scores and results use this grade scale:

| Grade | Percentage |
|---|---|
| A | ≥ 90 |
| B | ≥ 80 |
| C | ≥ 70 |
| D | ≥ 60 |
| E | ≥ 50 |
| F | < 50 |

## Notes on results

Term results (averages, class position, promotion status) are **generated in batches**,
not the instant a score is entered. An administrator runs the result-generation step (the
`generate_term_results` command or its Celery task). Until that runs for a term, the class
performance view falls back to live averages computed from raw scores, and position/grade
may show as pending or `—`.
