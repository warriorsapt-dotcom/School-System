import datetime
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import Teacher, Student
from classes.models import Class, Subject, ClassSubject, Term
from scores.models import Score

User = get_user_model()


class ClassPerformanceTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@test.com', username='admin@test.com',
            first_name='Admin', last_name='User',
            password='adminpass', role='admin',
        )

        teacher_user = User.objects.create_user(
            email='ct@test.com', username='ct@test.com',
            first_name='Alice', last_name='Mwangi',
            password='pass123', role='teacher',
        )
        self.teacher = Teacher.objects.create(user=teacher_user, employee_id='T001', is_class_teacher=True)

        other_teacher_user = User.objects.create_user(
            email='other@test.com', username='other@test.com',
            first_name='Bob', last_name='Jones',
            password='pass123', role='teacher',
        )
        self.other_teacher = Teacher.objects.create(user=other_teacher_user, employee_id='T002')

        self.cls = Class.objects.create(
            name='Form 1A', form_level=1, section='A', year=2025,
            class_teacher=self.teacher,
        )
        self.term = Term.objects.create(
            name='first', academic_year='2025/2026',
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 4, 30),
            is_current=True,
        )
        self.subject = Subject.objects.create(name='Mathematics', code='MATH')
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.cls, subject=self.subject,
            teacher=self.teacher, academic_year='2025/2026',
        )
        student_user = User.objects.create_user(
            email='stu@test.com', username='stu@test.com',
            first_name='James', last_name='Kariuki',
            password='pass123', role='student',
        )
        self.student = Student.objects.create(
            user=student_user, admission_number='ADM001', class_assigned=self.cls
        )
        Score.objects.create(
            student=self.student, class_subject=self.class_subject,
            subject=self.subject, assessment_type='test',
            marks_obtained=80, max_marks=100, term=self.term,
        )

    def test_class_teacher_can_view_performance(self):
        self.client.force_authenticate(user=self.teacher.user)
        res = self.client.get(f'/api/v1/classes/{self.cls.id}/student_performance/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_students'], 1)
        self.assertEqual(res.data['students'][0]['student_name'], 'James Kariuki')

    def test_admin_can_view_performance(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(f'/api/v1/classes/{self.cls.id}/student_performance/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_non_class_teacher_is_forbidden(self):
        self.client.force_authenticate(user=self.other_teacher.user)
        res = self.client.get(f'/api/v1/classes/{self.cls.id}/student_performance/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_me_returns_my_class(self):
        self.client.force_authenticate(user=self.teacher.user)
        res = self.client.get('/api/v1/users/teachers/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data['my_class'])
        self.assertEqual(res.data['my_class']['name'], 'Form 1A')

    def test_teacher_me_no_class_returns_null(self):
        self.client.force_authenticate(user=self.other_teacher.user)
        res = self.client.get('/api/v1/users/teachers/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data['my_class'])

    def test_scores_reflected_in_performance(self):
        self.client.force_authenticate(user=self.teacher.user)
        res = self.client.get(f'/api/v1/classes/{self.cls.id}/student_performance/')
        student = res.data['students'][0]
        self.assertAlmostEqual(float(student['average_percentage']), 80.0, places=1)
        self.assertIn('Mathematics', student['subjects'])


class ClassSubjectSelectionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@subject.test', username='subject-admin', password='Test123!', role='admin')
        self.client.force_authenticate(self.admin)
        self.cls = Class.objects.create(name='Form 3A', form_level=3, year=2026)
        self.subject = Subject.objects.create(name='Mathematics', code='MATH')
        self.assignment = ClassSubject.objects.create(class_obj=self.cls, subject=self.subject, academic_year='2026/2027')
        user = User.objects.create_user(email='irene@subject.test', username='irene', password='Test123!', role='student')
        self.student = Student.objects.create(user=user, admission_number='ADM020', class_assigned=self.cls)
        self.term = Term.objects.create(name='first', academic_year='2026/2027', start_date='2026-01-08', end_date='2026-04-12', is_current=True)

    def test_class_detail_returns_subject_ids_for_score_form(self):
        response = self.client.get(f'/api/v1/classes/{self.cls.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['class_subjects']), 1)
        assignment = response.data['class_subjects'][0]
        self.assertEqual(str(assignment['id']), str(self.assignment.pk))
        self.assertEqual(str(assignment['subject']), str(self.subject.pk))
        self.assertEqual(assignment['subject_name'], 'Mathematics')
        self.assertEqual(len(response.data['students']), 1)

    def test_empty_class_returns_empty_list(self):
        empty = Class.objects.create(name='Form 2B', form_level=2, year=2026)
        response = self.client.get(f'/api/v1/classes/{empty.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['class_subjects'], [])

    def test_class_subject_response_can_be_used_to_record_score(self):
        detail = self.client.get(f'/api/v1/classes/{self.cls.pk}/').data
        assignment = detail['class_subjects'][0]
        response = self.client.post('/api/v1/scores/', {
            'student': str(self.student.pk), 'class_subject': assignment['id'],
            'subject': assignment['subject'], 'assessment_type': 'exam',
            'marks_obtained': '78', 'max_marks': '100', 'term': str(self.term.pk),
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        score = Score.objects.get(pk=response.data['id'])
        self.assertEqual(score.subject, self.subject)
        self.assertEqual(score.percentage, 78)
