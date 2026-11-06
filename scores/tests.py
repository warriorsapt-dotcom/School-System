import datetime
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import Student, Teacher
from classes.models import Class, Subject, ClassSubject, Term
from scores.models import Score
from scores.models import SubjectPerformance, TermResult
from scores.utils import ResultCalculation
from django.core.management import call_command
from io import StringIO
from django.db.models.deletion import ProtectedError

User = get_user_model()


class ScoreTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@school.com', username='admin@school.com',
            first_name='Admin', last_name='User',
            password='adminpass123', role='admin',
        )
        teacher_user = User.objects.create_user(
            email='teacher@school.com', username='teacher@school.com',
            first_name='Jane', last_name='Doe',
            password='teacherpass123', role='teacher',
        )
        self.teacher = Teacher.objects.create(user=teacher_user, employee_id='T001')

        student_user = User.objects.create_user(
            email='student@school.com', username='student@school.com',
            first_name='John', last_name='Student',
            password='studentpass123', role='student',
        )
        self.cls = Class.objects.create(name='Form 1A', form_level=1, section='A', year=2024)
        self.student = Student.objects.create(
            user=student_user, admission_number='ADM001', class_assigned=self.cls
        )

        self.subject = Subject.objects.create(name='Mathematics', code='MATH')
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.cls, subject=self.subject,
            teacher=self.teacher, academic_year='2024/2025',
        )
        self.term = Term.objects.create(
            name='first', academic_year='2024/2025',
            start_date=datetime.date(2024, 1, 15),
            end_date=datetime.date(2024, 4, 15),
            is_current=True,
        )

    def _score_payload(self):
        return {
            'student': str(self.student.id),
            'class_subject': str(self.class_subject.id),
            'subject': str(self.subject.id),
            'assessment_type': 'test',
            'marks_obtained': '75',
            'max_marks': '100',
            'term': str(self.term.id),
        }

    def test_record_score_as_teacher(self):
        self.client.force_authenticate(user=self.teacher.user)
        res = self.client.post('/api/v1/scores/', self._score_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(res.data['percentage']), 75.0)
        self.assertEqual(res.data['grade'], 'C')

    def test_record_score_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/v1/scores/', self._score_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_record_score(self):
        self.client.force_authenticate(user=self.student.user)
        res = self.client.post('/api/v1/scores/', self._score_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_scores_authenticated(self):
        self.client.force_authenticate(user=self.student.user)
        res = self.client.get('/api/v1/scores/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_student_sees_only_own_scores(self):
        # Create a second student
        other_user = User.objects.create_user(
            email='other@school.com', username='other@school.com',
            first_name='Other', last_name='Student',
            password='pass123', role='student',
        )
        other_student = Student.objects.create(
            user=other_user, admission_number='ADM002', class_assigned=self.cls
        )
        # Score for self.student
        Score.objects.create(
            student=self.student, class_subject=self.class_subject,
            subject=self.subject, assessment_type='test',
            marks_obtained=80, max_marks=100, term=self.term,
        )
        # Score for other_student
        Score.objects.create(
            student=other_student, class_subject=self.class_subject,
            subject=self.subject, assessment_type='test',
            marks_obtained=60, max_marks=100, term=self.term,
        )
        self.client.force_authenticate(user=self.student.user)
        res = self.client.get('/api/v1/scores/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # res.data returns UUID objects, so compare via str()
        ids = [str(s['student']) for s in res.data['results']]
        self.assertTrue(all(i == str(self.student.id) for i in ids),
                        f'Student saw another student\'s score. IDs returned: {ids}')

    def test_percentage_calculated_on_save(self):
        self.client.force_authenticate(user=self.teacher.user)
        payload = self._score_payload()
        payload['marks_obtained'] = '45'
        payload['max_marks'] = '50'
        res = self.client.post('/api/v1/scores/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(res.data['percentage']), 90.0)
        self.assertEqual(res.data['grade'], 'A')

    def test_command_builds_results_from_scores_without_existing_summaries(self):
        Score.objects.create(student=self.student, class_subject=self.class_subject,
                             subject=self.subject, assessment_type='test',
                             marks_obtained=40, max_marks=50, term=self.term)
        Score.objects.create(student=self.student, class_subject=self.class_subject,
                             subject=self.subject, assessment_type='exam',
                             marks_obtained=80, max_marks=100, term=self.term)
        output = StringIO()
        call_command('generate_term_results', term='first', class_name='Form 1A',
                     year='2024/2025', stdout=output)
        self.assertIn('1 students', output.getvalue())
        result = TermResult.objects.get(student=self.student)
        self.assertEqual(result.total_marks, 120)
        self.assertEqual(result.total_max_marks, 150)
        self.assertEqual(result.average_percentage, 80)
        self.assertEqual(result.position_in_class, 1)
        self.assertEqual(SubjectPerformance.objects.get().number_of_assessments, 2)
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get('/api/v1/results/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_regeneration_updates_existing_results_and_excludes_unapproved_scores(self):
        score = Score.objects.create(student=self.student, class_subject=self.class_subject,
                                     subject=self.subject, assessment_type='test',
                                     marks_obtained=80, max_marks=100, term=self.term)
        ResultCalculation.generate_term_results(self.cls, self.term)
        score.marks_obtained = 60
        score.save()
        ResultCalculation.generate_term_results(self.cls, self.term)
        self.assertEqual(TermResult.objects.get().average_percentage, 60)
        self.assertEqual(SubjectPerformance.objects.count(), 1)
        score.is_approved = False
        score.save()
        self.assertEqual(ResultCalculation.generate_term_results(self.cls, self.term), [])
        self.assertFalse(TermResult.objects.exists())
        self.assertFalse(SubjectPerformance.objects.exists())

    def test_progress_follows_student_across_years_and_preserves_old_class(self):
        Score.objects.create(student=self.student, class_subject=self.class_subject,
                             subject=self.subject, assessment_type='exam',
                             marks_obtained=60, max_marks=100, term=self.term)
        ResultCalculation.generate_term_results(self.cls, self.term)
        next_class = Class.objects.create(name='Form 2A', form_level=2, year=2025)
        next_term = Term.objects.create(name='first', academic_year='2025/2026',
                                       start_date=datetime.date(2025,1,15), end_date=datetime.date(2025,4,15))
        self.student.class_assigned = next_class
        self.student.save()
        TermResult.objects.create(student=self.student, class_obj=next_class, term=next_term,
                                  average_percentage=80, overall_grade='B')
        # Rebuilding the old class still includes its former student.
        rebuilt = ResultCalculation.generate_term_results(self.cls, self.term)
        self.assertEqual(len(rebuilt), 1)
        self.assertEqual(rebuilt[0].total_students_in_class, 1)
        self.cls.name = 'Renamed class'
        self.cls.save()
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(f'/api/v1/users/students/{self.student.pk}/progress/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['class_name'] for r in response.data], ['Form 1A','Form 2A'])
        self.assertEqual([r['academic_year'] for r in response.data], ['2024/2025','2025/2026'])
        self.assertEqual([r['average_percentage'] for r in response.data], [60,80])
        self.assertEqual(response.data[1]['change'], 20)
        self.assertIsNone(response.data[0]['change'])
        with self.assertRaises(ProtectedError):
            self.cls.delete()
        with self.assertRaises(ProtectedError):
            self.term.delete()

    def test_grade_ten_and_student_progress_privacy(self):
        grade = Class(name='Grade 10A', form_level=10, year=2033)
        grade.full_clean(exclude=['class_teacher'])
        grade.save()
        other_user = User.objects.create_user(email='private@school.com', username='private', role='student')
        other = Student.objects.create(user=other_user, admission_number='PRIVATE', class_assigned=grade)
        self.client.force_authenticate(user=self.student.user)
        self.assertEqual(self.client.get(f'/api/v1/users/students/{other.pk}/progress/').status_code, 404)
        self.assertEqual(self.client.get('/api/v1/progress/chart/', {'student':str(other.pk)}).status_code, 404)

    def test_all_grade_levels_can_be_tracked_without_progress_logs(self):
        for level in range(1,11):
            cls = Class.objects.create(name=f'Grade {level}', form_level=level, year=2020+level)
            term = Term.objects.create(name='second', academic_year=f'{2020+level}/{2021+level}',
                                       start_date=datetime.date(2020+level,1,15), end_date=datetime.date(2020+level,4,15))
            TermResult.objects.create(student=self.student, class_obj=cls, term=term, average_percentage=50+level)
        self.client.force_authenticate(user=self.student.user)
        data = self.client.get(f'/api/v1/users/students/{self.student.pk}/progress/').data
        self.assertEqual([r['level'] for r in data], list(range(1,11)))
        self.assertEqual(len(data), 10)
