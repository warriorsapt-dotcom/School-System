"""
Seed the database with realistic test data.

Usage:
    python manage.py seed_data           # create everything
    python manage.py seed_data --timetable-only  # add lessons to existing demo classes
    python manage.py seed_data --clear   # wipe data first, then seed
"""

import random
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


SUBJECTS = [
    ('Mathematics',    'MATH', True),
    ('English',        'ENG',  True),
    ('Biology',        'BIO',  True),
    ('Chemistry',      'CHEM', True),
    ('Physics',        'PHY',  True),
    ('History',        'HIST', False),
    ('Geography',      'GEO',  False),
    ('Computer Studies','CS',  False),
]

CLASSES = [
    ('Form 1A', 1, 'A'),
    ('Form 1B', 1, 'B'),
    ('Form 2A', 2, 'A'),
    ('Form 2B', 2, 'B'),
    ('Form 3A', 3, 'A'),
]

TEACHERS = [
    ('Alice',  'Mwangi',    'T001', 'B.Ed Mathematics',    'Mathematics'),
    ('Brian',  'Otieno',    'T002', 'B.Ed English',         'English'),
    ('Carol',  'Njoroge',   'T003', 'M.Sc Biology',         'Biology'),
    ('David',  'Kamau',     'T004', 'M.Sc Chemistry',       'Chemistry'),
    ('Eve',    'Wanjiku',   'T005', 'B.Ed Physics',         'Physics'),
    ('Frank',  'Mutua',     'T006', 'B.Ed Humanities',      'History & Geography'),
    ('Grace',  'Achieng',   'T007', 'B.Sc Computer Science','Computer Studies'),
]

STUDENTS = [
    # (first, last, dob, parent_name, parent_contact)
    ('James',    'Kariuki',  '2009-03-14', 'Peter Kariuki',   '0712345001'),
    ('Mercy',    'Wanjiru',  '2009-07-22', 'Ann Wanjiru',     '0712345002'),
    ('Kevin',    'Otieno',   '2010-01-08', 'John Otieno',     '0712345003'),
    ('Faith',    'Chebet',   '2009-11-30', 'Rose Chebet',     '0712345004'),
    ('Samuel',   'Njoroge',  '2010-05-17', 'David Njoroge',   '0712345005'),
    ('Purity',   'Waweru',   '2009-09-03', 'Grace Waweru',    '0712345006'),
    ('Daniel',   'Maina',    '2010-02-25', 'Lucy Maina',      '0712345007'),
    ('Sharon',   'Adhiambo', '2009-06-12', 'Thomas Adhiambo', '0712345008'),
    ('Emmanuel', 'Kimani',   '2010-08-19', 'Mary Kimani',     '0712345009'),
    ('Vivian',   'Kamau',    '2009-04-27', 'Stephen Kamau',   '0712345010'),
    ('Brian',    'Ochieng',  '2010-12-05', 'Jane Ochieng',    '0712345011'),
    ('Sandra',   'Muthoni',  '2009-10-14', 'Paul Muthoni',    '0712345012'),
    ('George',   'Kiprotich','2010-03-31', 'Esther Kiprotich','0712345013'),
    ('Agnes',    'Nekesa',   '2009-08-08', 'Isaac Nekesa',    '0712345014'),
    ('Michael',  'Gitonga',  '2010-06-23', 'Sarah Gitonga',   '0712345015'),
    ('Lydia',    'Auma',     '2009-02-16', 'Robert Auma',     '0712345016'),
    ('Victor',   'Mwenda',   '2010-09-09', 'Patricia Mwenda', '0712345017'),
    ('Esther',   'Waithaka', '2009-12-01', 'Daniel Waithaka', '0712345018'),
    ('Collins',  'Barasa',   '2010-04-14', 'Beatrice Barasa', '0712345019'),
    ('Irene',    'Wambua',   '2009-07-07', 'Francis Wambua',  '0712345020'),
]

ATT_STATUSES = ['present', 'present', 'present', 'present', 'absent', 'late']

ASSESSMENT_TYPES = ['test', 'exam', 'assignment', 'class_work']


def rnd_score(low=35, high=98):
    return Decimal(str(round(random.uniform(low, high), 1)))


class Command(BaseCommand):
    help = 'Seed the database with realistic test data'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('--timetable-only', action='store_true',
                          help='Add only weekly lessons for the existing sample class assignments')
        mode.add_argument(
            '--clear', action='store_true',
            help='Delete existing seeded data before inserting'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['timetable_only']:
            self._create_timetable()
            return
        if options['clear']:
            self._clear()

        from users.models import CustomUser, Teacher, Student
        from classes.models import Class, Subject, ClassSubject, Term
        from attendance.models import Attendance
        from scores.models import Score

        self.stdout.write(self.style.MIGRATE_HEADING('-- Creating subjects...'))
        subjects = self._create_subjects()

        self.stdout.write(self.style.MIGRATE_HEADING('-- Creating classes...'))
        classes = self._create_classes()

        self.stdout.write(self.style.MIGRATE_HEADING('-- Creating teachers...'))
        teachers = self._create_teachers()

        self.stdout.write(self.style.MIGRATE_HEADING('-- Creating term...'))
        term = self._create_term()

        self.stdout.write(self.style.MIGRATE_HEADING('-- Assigning teachers to subjects & classes...'))
        class_subjects = self._assign_teachers(classes, subjects, teachers)
        self._create_timetable()

        self.stdout.write(self.style.MIGRATE_HEADING('-- Creating students...'))
        students = self._create_students(classes)

        self.stdout.write(self.style.MIGRATE_HEADING('-- Marking attendance (last 30 school days)...'))
        self._create_attendance(students, classes, term, teachers)

        self.stdout.write(self.style.MIGRATE_HEADING('-- Recording scores...'))
        self._create_scores(students, class_subjects, term)

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeded: {len(subjects)} subjects, {len(classes)} classes, '
            f'{len(teachers)} teachers, {len(students)} students, 1 term.\n'
            f'  Teachers: teacher01@school.com ... teacher07@school.com  /  pass: school123\n'
            f'  Students: student01@school.com ... student20@school.com  /  pass: school123\n'
            f'  Admin:    admin@school.com  /  qazwsx123!\n'
        ))

    # ── helpers ──────────────────────────────────────────────────────────

    def _create_timetable(self):
        from classes.models import ClassSubject, Lesson
        from classes.workspace import LessonSerializer

        year = datetime.date.today().year
        class_names = [name for name, _, _ in CLASSES]
        assignments = ClassSubject.objects.select_related('class_obj', 'subject').filter(
            class_obj__name__in=class_names, class_obj__year=year,
            academic_year=f'{year}/{year+1}', teacher__isnull=False,
        )
        by_class_subject = {(a.class_obj.name, a.subject.code): a for a in assignments}
        if not by_class_subject:
            raise CommandError('No sample class assignments found for this year. Run seed_data first.')

        periods = [('08:00', '08:45'), ('08:50', '09:35'), ('10:00', '10:45'), ('10:50', '11:35')]
        # History and geography share a teacher, so alternate them within one rotation slot.
        rotation = ['MATH', 'ENG', 'BIO', 'CHEM', 'PHY', 'HIST', 'CS']
        created = skipped = 0
        for weekday in range(1, 6):
            for period, (starts, ends) in enumerate(periods):
                for index, name in enumerate(class_names):
                    position = (weekday - 1) * len(periods) + period + index
                    code = rotation[position % len(rotation)]
                    if code == 'HIST' and (position // len(rotation)) % 2:
                        code = 'GEO'
                    assignment = by_class_subject.get((name, code))
                    if not assignment or Lesson.objects.filter(
                        assignment=assignment, weekday=weekday, starts=starts, ends=ends
                    ).exists():
                        skipped += 1
                        continue
                    lesson = LessonSerializer(data={'assignment': assignment.pk, 'weekday': weekday,
                                                    'starts': starts, 'ends': ends, 'room': name})
                    if not lesson.is_valid():
                        if any(error.code == 'overlap' for error in lesson.errors.get('non_field_errors', [])):
                            skipped += 1
                            continue
                        raise CommandError(str(lesson.errors))
                    lesson.save()
                    created += 1
        self.stdout.write(f'Timetable: {created} lessons added; {skipped} existing, unavailable or conflicting slots skipped.')

    def _clear(self):
        from users.models import CustomUser
        from attendance.models import Attendance
        from scores.models import Score

        self.stdout.write(self.style.WARNING('Clearing seeded data...'))
        Score.objects.all().delete()
        Attendance.objects.all().delete()
        # Remove non-superuser users (keeps the admin superuser)
        CustomUser.objects.filter(is_superuser=False).delete()
        from classes.models import Class, Subject, ClassSubject, Term
        ClassSubject.objects.all().delete()
        Class.objects.all().delete()
        Subject.objects.all().delete()
        Term.objects.all().delete()
        self.stdout.write(self.style.WARNING('  Done clearing.\n'))

    def _create_subjects(self):
        from classes.models import Subject
        result = []
        for name, code, compulsory in SUBJECTS:
            subj, created = Subject.objects.get_or_create(
                code=code,
                defaults={'name': name, 'is_compulsory': compulsory, 'is_active': True}
            )
            result.append(subj)
            self.stdout.write(f'  {"+" if created else "·"} {subj.name}')
        return result

    def _create_classes(self):
        from classes.models import Class
        result = []
        year = datetime.date.today().year
        for name, form, section in CLASSES:
            cls, created = Class.objects.get_or_create(
                name=name, year=year,
                defaults={'form_level': form, 'section': section, 'capacity': 40, 'is_active': True}
            )
            result.append(cls)
            self.stdout.write(f'  {"+" if created else "·"} {cls.name}')
        return result

    def _create_teachers(self):
        from users.models import CustomUser, Teacher
        result = []
        for i, (first, last, emp_id, qual, spec) in enumerate(TEACHERS, start=1):
            email = f'teacher{i:02d}@school.com'
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first,
                    'last_name': last,
                    'role': 'teacher',
                    'phone_number': f'072000{i:04d}',
                }
            )
            if created:
                user.set_password('school123')
                user.save()
            teacher, _ = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': emp_id,
                    'qualification': qual,
                    'subject_specialization': spec,
                    'hire_date': datetime.date(2020, 1, 15),
                    'is_class_teacher': (i <= len(CLASSES)),
                    'is_active': True,
                }
            )
            result.append(teacher)
            self.stdout.write(f'  {"+" if created else "·"} {first} {last} <{email}>')
        return result

    def _create_term(self):
        from classes.models import Term
        year = datetime.date.today().year
        acad = f'{year}/{year+1}'
        start = datetime.date(year, 1, 8)
        end   = datetime.date(year, 4, 12)
        term, created = Term.objects.get_or_create(
            name='first', academic_year=acad,
            defaults={'start_date': start, 'end_date': end, 'is_current': True, 'is_active': True}
        )
        if created:
            self.stdout.write(f'  + {term}')
        else:
            self.stdout.write(f'  · {term} (exists)')
        return term

    def _assign_teachers(self, classes, subjects, teachers):
        from classes.models import ClassSubject
        year = datetime.date.today().year
        acad = f'{year}/{year+1}'

        # Map subject name → teacher
        subj_teacher_map = {
            'Mathematics':     teachers[0],
            'English':         teachers[1],
            'Biology':         teachers[2],
            'Chemistry':       teachers[3],
            'Physics':         teachers[4],
            'History':         teachers[5],
            'Geography':       teachers[5],
            'Computer Studies':teachers[6],
        }

        # Assign the first N teachers as class teachers (one per class)
        for i, cls in enumerate(classes):
            if i < len(teachers):
                if cls.class_teacher_id != teachers[i].id:
                    cls.class_teacher = teachers[i]
                    cls.save(update_fields=['class_teacher'])
                    teachers[i].is_class_teacher = True
                    teachers[i].save(update_fields=['is_class_teacher'])
                    self.stdout.write(f'  Assigned {teachers[i]} as class teacher of {cls.name}')

        result = []
        for cls in classes:
            for subj in subjects:
                teacher = subj_teacher_map.get(subj.name, teachers[0])
                cs, created = ClassSubject.objects.get_or_create(
                    class_obj=cls, subject=subj, academic_year=acad,
                    defaults={'teacher': teacher}
                )
                result.append(cs)
        self.stdout.write(f'  {len(result)} class-subject assignments')
        return result

    def _create_students(self, classes):
        from users.models import CustomUser, Student
        result = []
        cls_cycle = classes * (len(STUDENTS) // len(classes) + 1)

        for i, (first, last, dob, parent, contact) in enumerate(STUDENTS, start=1):
            email = f'student{i:02d}@school.com'
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first,
                    'last_name': last,
                    'role': 'student',
                }
            )
            if created:
                user.set_password('school123')
                user.save()
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    'admission_number': f'ADM2024{i:03d}',
                    'class_assigned': cls_cycle[i - 1],
                    'date_of_birth': datetime.date.fromisoformat(dob),
                    'parent_name': parent,
                    'parent_contact': contact,
                    'parent_email': f'parent{i:02d}@mail.com',
                    'is_active': True,
                }
            )
            result.append(student)
            self.stdout.write(f'  {"+" if created else "."} {first} {last} -> {student.class_assigned.name}')
        return result

    def _create_attendance(self, students, classes, term, teachers):
        from attendance.models import Attendance

        today = datetime.date.today()
        # Collect the last 30 weekdays
        school_days = []
        d = today - datetime.timedelta(days=1)
        while len(school_days) < 30:
            if d.weekday() < 5:  # Mon–Fri
                school_days.append(d)
            d -= datetime.timedelta(days=1)

        created_count = 0
        for student in students:
            cls = student.class_assigned
            teacher = (
                cls.class_teacher
                or next((t for t in teachers if t.is_class_teacher), teachers[0])
            )
            for day in school_days:
                if Attendance.objects.filter(student=student, date=day).exists():
                    continue
                status = random.choice(ATT_STATUSES)
                Attendance.objects.create(
                    student=student,
                    class_obj=cls,
                    date=day,
                    status=status,
                    term=term,
                    teacher=teacher,
                )
                created_count += 1
        self.stdout.write(f'  {created_count} attendance records')

    def _create_scores(self, students, class_subjects, term):
        from scores.models import Score
        from classes.models import ClassSubject

        created_count = 0
        cs_map = {}
        for cs in class_subjects:
            cs_map.setdefault(cs.class_obj_id, {})[cs.subject_id] = cs

        for student in students:
            cls_id = student.class_assigned_id
            per_class = cs_map.get(cls_id, {})

            for subject_id, cs in per_class.items():
                for atype in ASSESSMENT_TYPES:
                    # Avoid re-creating if already present
                    if Score.objects.filter(student=student, class_subject=cs, assessment_type=atype, term=term).exists():
                        continue

                    # Give each student a consistent "ability level" for variety
                    ability = random.gauss(70, 15)
                    marks = max(5, min(100, Decimal(str(round(ability + random.gauss(0, 8), 1)))))
                    Score.objects.create(
                        student=student,
                        class_subject=cs,
                        subject=cs.subject,
                        assessment_type=atype,
                        marks_obtained=marks,
                        max_marks=Decimal('100'),
                        term=term,
                        is_approved=True,
                    )
                    created_count += 1

        self.stdout.write(f'  {created_count} score records')
