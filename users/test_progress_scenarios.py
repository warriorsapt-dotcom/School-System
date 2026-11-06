from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from classes.models import Class, Subject, Term
from scores.models import Score, TermResult, SubjectPerformance
from scores.progress import student_progress
from users.models import CustomUser, Student


class ProgressScenarioTests(TestCase):
    def seed(self):
        call_command('seed_progress_scenarios', end_year=2026, stdout=StringIO())

    def student(self, scenario):
        return Student.objects.get(user__email=f'progress.{scenario}.2026@school.test')

    def test_all_scenarios_and_repeatability_preserve_school_records(self):
        current = Term.objects.create(name='first', academic_year='2026/2027',
                                      start_date=date(2026,1,15), end_date=date(2026,4,20), is_current=True)
        real_class = Class.objects.create(name='Real Form 1', form_level=1, year=2026)
        real_user = CustomUser.objects.create_user(email='real@school.test', username='real', password='Unchanged123!')
        real_student = Student.objects.create(user=real_user, admission_number='REAL1', class_assigned=real_class)
        self.seed()
        expected = {'form':12,'primary':30,'declining':12,'steady':12,'repeat':15,'transfer':12,'missing':5,'new':0}
        for key, count in expected.items():
            self.assertEqual(self.student(key).term_results.count(), count, key)
        form = student_progress(self.student('form'))
        self.assertEqual([r['level'] for r in form], [1]*3+[2]*3+[3]*3+[4]*3)
        self.assertGreater(form[-1]['average_percentage'], form[0]['average_percentage'])
        primary = student_progress(self.student('primary'))
        self.assertEqual(sorted({r['level'] for r in primary}), list(range(1,11)))
        decline = student_progress(self.student('declining'))
        self.assertLess(decline[-1]['average_percentage'], decline[0]['average_percentage'])
        self.assertEqual(len({r['average_percentage'] for r in student_progress(self.student('steady'))}), 1)
        repeated = student_progress(self.student('repeat'))
        self.assertEqual(len({r['academic_year'] for r in repeated if r['level']==2}), 2)
        self.assertEqual(repeated[3]['status'], 'retained')
        transfer = student_progress(self.student('transfer'))
        self.assertNotEqual(transfer[0]['class_name'], transfer[1]['class_name'])
        self.assertEqual(transfer[0]['academic_year'], transfer[1]['academic_year'])
        missing = student_progress(self.student('missing'))
        self.assertNotIn('2025/2026', {r['academic_year'] for r in missing})
        self.assertEqual(len(missing), 5)
        models = [CustomUser, Student, Class, Subject, Term, Score, TermResult, SubjectPerformance]
        counts = [model.objects.count() for model in models]
        demo = self.student('form').user
        demo.set_password('ChangedByTester123!')
        demo.save()
        self.seed()
        self.assertEqual(counts, [model.objects.count() for model in models])
        demo.refresh_from_db()
        self.assertTrue(demo.check_password('ChangedByTester123!'))
        current.refresh_from_db()
        self.assertTrue(current.is_current)
        self.assertEqual(current.start_date, date(2026,1,15))
        real_student.refresh_from_db()
        self.assertEqual(real_student.class_assigned_id, real_class.pk)
        self.assertFalse(real_student.term_results.exists())
        real_user.refresh_from_db()
        self.assertTrue(real_user.check_password('Unchanged123!'))
