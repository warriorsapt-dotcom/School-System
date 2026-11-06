"""Add isolated, repeatable academic-history examples without clearing school data."""
import secrets
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from classes.models import Class, ClassSubject, Subject, Term
from scores.models import Score
from scores.utils import ResultCalculation
from users.models import CustomUser, Student, Teacher


SCENARIOS = [
    ('form', 'Improving', 'Form', [1, 2, 3, 4]),
    ('primary', 'Primary journey', 'Grade', list(range(1, 11))),
    ('declining', 'Declining', 'Form', [1, 2, 3, 4]),
    ('steady', 'Steady', 'Form', [1, 2, 3, 4]),
    ('repeat', 'Repeated class', 'Form', [1, 2, 2, 3, 4]),
    ('transfer', 'Class transfer', 'Form', [1, 2, 3, 4]),
    ('missing', 'Missing terms', 'Form', [1, 2, 3]),
    ('new', 'New admission', 'Form', [1]),
]


class Command(BaseCommand):
    help = 'Create labelled demo students covering academic-progress scenarios. Safe to rerun; does not clear data.'

    def add_arguments(self, parser):
        parser.add_argument('--end-year', type=int, default=timezone.localdate().year,
                            help='Final calendar year of the histories (default: current year). Reuse it when rerunning.')

    @transaction.atomic
    def handle(self, *args, **options):
        end_year = options['end_year']
        if not 2000 <= end_year <= 2090:
            raise CommandError('Choose an end year between 2000 and 2090.')
        marker = f'Academic progress demo {end_year}'
        password = secrets.token_urlsafe(12)
        new_logins = []

        def account(key, label, role):
            email = f'progress.{key}.{end_year}@school.test'
            username = f'progress-demo-{end_year}-{key}'
            user, created = CustomUser.objects.get_or_create(email=email, defaults={
                'username': username, 'first_name': 'Demo', 'last_name': label, 'role': role,
            })
            if user.username != username or user.role != role:
                raise CommandError(f'{email} already belongs to another account; nothing was changed.')
            if created:
                user.set_password(password)
                user.save(update_fields=['password'])
                new_logins.append(email)
            return user

        teacher_user = account('teacher', 'Progress Teacher', 'teacher')
        teacher, _ = Teacher.objects.get_or_create(user=teacher_user, defaults={
            'employee_id': f'DP-{end_year}-TEACHER', 'is_class_teacher': True,
        })
        subjects = []
        for code, name in [('M', 'Mathematics'), ('E', 'English'), ('S', 'Science')]:
            subject, _ = Subject.objects.get_or_create(code=f'DP{end_year}{code}', defaults={
                'name': f'Demo Progress {end_year} {name}', 'description': marker,
            })
            if subject.description != marker:
                raise CommandError('A demo subject identifier is already in use; nothing was changed.')
            subjects.append(subject)

        def school_class(stage, level, year, section='A'):
            name = f'Demo {end_year} · {stage} {level}{section} · {year}'
            cls, _ = Class.objects.get_or_create(name=name, defaults={
                'form_level': level, 'section': section, 'year': year,
                'class_teacher': teacher, 'description': marker,
            })
            if cls.description != marker:
                raise CommandError('A demo class identifier is already in use; nothing was changed.')
            return cls

        pairs = {}
        summary = []
        for key, label, stage, levels in SCENARIOS:
            user = account(key, label, 'student')
            start_year = end_year - len(levels) + 1
            final_section = 'B' if key == 'transfer' else 'A'
            current_class = school_class(stage, levels[-1], end_year, final_section)
            student, _ = Student.objects.get_or_create(user=user, defaults={
                'admission_number': f'DP-{end_year}-{key.upper()}',
                'admission_date': date(start_year, 1, 8), 'class_assigned': current_class,
            })
            if student.admission_number != f'DP-{end_year}-{key.upper()}':
                raise CommandError('A demo student account has a different admission number; nothing was changed.')
            result_count = 0
            for year_index, level in enumerate(levels):
                year = start_year + year_index
                if key == 'new' or (key == 'missing' and year_index == 1):
                    continue
                for term_index, term_name in enumerate(['first', 'second', 'third']):
                    if key == 'missing' and year_index == 2 and term_index == 1:
                        continue
                    section = 'B' if key == 'transfer' and (year_index > 0 or term_index > 0) else 'A'
                    cls = school_class(stage, level, year, section)
                    academic_year = f'{year}/{year+1}'
                    term, _ = Term.objects.get_or_create(name=term_name, academic_year=academic_year, defaults={
                        'start_date': date(year, [1, 5, 9][term_index], 8),
                        'end_date': date(year, [4, 8, 12][term_index], 12),
                        'is_current': False,
                    })
                    step = year_index * 3 + term_index
                    if key == 'declining':
                        mark = 85 - step * 4
                    elif key == 'steady':
                        mark = 72
                    elif key == 'repeat':
                        mark = 42 if year_index == 1 else 60 + year_index * 5 + term_index
                    elif key == 'primary':
                        mark = 55 + step
                    else:
                        mark = 55 + step * 3
                    for subject_index, subject in enumerate(subjects):
                        assignment, _ = ClassSubject.objects.get_or_create(
                            class_obj=cls, subject=subject, academic_year=academic_year,
                            defaults={'teacher': teacher})
                        Score.objects.get_or_create(student=student, class_subject=assignment,
                            subject=subject, term=term, assessment_type='exam',
                            defaults={'marks_obtained': mark + subject_index - 1,
                                      'max_marks': 100, 'is_approved': True, 'remarks': marker})
                    pairs[(cls.pk, term.pk)] = (cls, term)
                    result_count += 1
            summary.append(f'{user.email}: {label} — {result_count} term results')

        # Generate after all scores are present so class positions include every demo peer.
        for cls, term in pairs.values():
            ResultCalculation.generate_term_results(cls, term)

        self.stdout.write(self.style.SUCCESS(f'Academic-progress scenarios ready for end year {end_year}.'))
        for line in summary:
            self.stdout.write(line)
        self.stdout.write(f'Teacher: {teacher_user.email}')
        if new_logins:
            self.stdout.write('New accounts: ' + ', '.join(new_logins))
            self.stdout.write(f'Password for the {len(new_logins)} NEW demo accounts: {password}')
        else:
            self.stdout.write('No new accounts. Existing passwords and student class assignments were preserved.')
        self.stdout.write('Existing school terms were reused without changing the current term. All demo classes and subjects are labelled Demo.')
