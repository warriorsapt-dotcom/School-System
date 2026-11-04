from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from classes.models import Class, ClassSubject, Subject
from users.models import Student, Teacher
from .models import Attendance


class AttendanceHistoryTests(APITestCase):
    def setUp(self):
        def user(name, role):
            return get_user_model().objects.create_user(
                username=name, email=f'{name}@test.com', password='Test123!', role=role)
        self.teacher = Teacher.objects.create(user=user('teacher', 'teacher'), employee_id='T1')
        self.other = Teacher.objects.create(user=user('other', 'teacher'), employee_id='T2')
        self.admin = user('admin', 'admin')
        self.cls = Class.objects.create(name='Form 1A', form_level=1, class_teacher=self.teacher)
        self.student = Student.objects.create(user=user('student', 'student'), admission_number='A1', class_assigned=self.cls)
        self.url = f'/api/v1/users/students/{self.student.pk}/attendance_history/'
        for i in range(25):
            Attendance.objects.create(student=self.student, class_obj=self.cls, teacher=self.teacher,
                                      date=date(2026, 1, 1) + timedelta(days=i),
                                      status='absent' if i == 0 else 'present', remarks='Recorded in register')
        self.client.force_authenticate(self.teacher.user)

    def test_class_teacher_can_read_paginated_history_newest_first(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(response.data['results'][0]['date'], '2026-01-25')
        self.assertEqual(response.data['results'][0]['remarks'], 'Recorded in register')
        self.assertIsNotNone(response.data['next'])
        second = self.client.get(self.url, {'page': 2})
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['results'])

    def test_subject_teacher_can_read_history(self):
        ClassSubject.objects.create(class_obj=self.cls, teacher=self.other,
                                    subject=Subject.objects.create(name='Math'))
        self.client.force_authenticate(self.other.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_other_teacher_and_student_cannot_read_history(self):
        self.client.force_authenticate(self.other.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_filters_are_inclusive_and_validate_dates(self):
        response = self.client.get(self.url, {'start_date': '2026-01-01', 'end_date': '2026-01-01', 'status': 'absent'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'status': 'medical'}).data['count'], 0)
        for params in [{'start_date': 'bad'}, {'status': 'bad'}, {'start_date': '2026-02-01', 'end_date': '2026-01-01'}]:
            self.assertEqual(self.client.get(self.url, params).status_code, 400)

    def test_admin_can_read_and_other_students_records_are_excluded(self):
        another = Student.objects.create(user=get_user_model().objects.create_user(
            username='second', email='second@test.com', role='student'), admission_number='A2', class_assigned=self.cls)
        Attendance.objects.create(student=another, class_obj=self.cls, date='2026-02-01')
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.url).data['count'], 25)
