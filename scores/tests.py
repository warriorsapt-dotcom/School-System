import datetime
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import Student, Teacher
from classes.models import Class, Subject, ClassSubject, Term
from scores.models import Score

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
