# Academic progress demonstration data

Run in the school project directory with its virtual environment active:

```bash
python manage.py seed_progress_scenarios --end-year 2026
```

This adds eight clearly labelled demo students, one demo teacher, demo classes and three demo subjects. It creates actual scores and generates the results used by the progress screens. It does not clear school data, change the current term or reset existing passwords. Existing terms are reused without editing them. Repeating the command with the **same end year** does not duplicate its accounts, scores or results. A different end year creates a separate set of demo accounts.

The command prints a generated password for newly created demo accounts. Save it when first running the command. Reruns keep their existing passwords. These are synthetic histories for testing; historical exam scores deliberately appear in past terms even though their entry timestamp is the day the command is run.

| Scenario | Student login | Expected history |
| --- | --- | --- |
| Improving secondary student | progress.form.2026@school.test | Form 1–4, 2023–2026, all 12 terms, rising averages |
| Complete primary journey | progress.primary.2026@school.test | Grade 1–10, 2017–2026, all 30 terms |
| Declining performance | progress.declining.2026@school.test | Form 1–4, 12 terms, falling averages and failed subjects |
| Steady performance | progress.steady.2026@school.test | Form 1–4, 12 terms, stable 72% average |
| Repeated class | progress.repeat.2026@school.test | Five years, Form 2 in two consecutive years, recovery after poor results |
| Class/stream transfer | progress.transfer.2026@school.test | Form 1A in the first term, Form 1B from the second term, then through Form 4B |
| Incomplete history | progress.missing.2026@school.test | Five recorded terms; the middle year and one final-year term are missing |
| Newly admitted student | progress.new.2026@school.test | Assigned Form 1, no scores or results yet |

Teacher login: **progress.teacher.2026@school.test**. The teacher is assigned to the demo classes. This command does not create an administrator account; use your existing administrator to inspect all scenarios.

## Check the results

1. As a demo student, open **My Results → View progress across all years**.
2. Check the graph, year averages, class labels, rankings and changes between terms.
3. For the new admission account, expect the friendly empty results message.
4. As the administrator, open **Results**, choose the relevant demo class and academic term, and use **View progress** beside the student.
5. Check that the repeated class remains visible in both academic years and that missing periods are not represented as zero scores.
6. Log in as a second demo student and confirm only that student's results appear.

Changing the `--end-year` value changes the years embedded in the logins and identifiers above. The same student account is used across each scenario's full history; no automatic promotion or real enrolment changes are performed.

These demos are for academic progress. They do not add timetable lessons, attendance records or assignment-deadline examples. For normal timetable demo data, the existing `seed_data --timetable-only` command remains available.
