from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from users.models import Student, Teacher
from .models import Class, ClassSubject, Subject


class SchoolWorkspaceTests(APITestCase):
    def setUp(self):
        def account(name, role):
            return get_user_model().objects.create_user(username=name, email=name+'@school.test', role=role)
        self.admin = account('head', 'admin')
        self.teacher = Teacher.objects.create(user=account('mary', 'teacher'), employee_id='T1')
        self.student = account('sam', 'student')
        self.other = account('pat', 'student')
        self.cls = Class.objects.create(name='Class A', form_level=1)
        self.second = Class.objects.create(name='Class B', form_level=1)
        Student.objects.create(user=self.student, class_assigned=self.cls, admission_number='A01')
        Student.objects.create(user=self.other, class_assigned=self.second, admission_number='B01')
        self.subject = Subject.objects.create(name='Mathematics')
        self.assignment = ClassSubject.objects.create(class_obj=self.cls, teacher=self.teacher, subject=self.subject)
        self.client.force_authenticate(self.admin)

    def test_timetable_visibility_and_conflicts(self):
        url = '/api/v1/timetable/'
        data = {'assignment': self.assignment.pk, 'weekday': 1, 'starts': '08:00', 'ends': '08:45'}
        created = self.client.post(url, data)
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(self.client.post(url, data).status_code, 400)
        second = ClassSubject.objects.create(class_obj=self.second, teacher=self.teacher, subject=self.subject)
        self.assertEqual(self.client.post(url, dict(data, assignment=second.pk)).status_code, 400)
        self.assertEqual(self.client.post(url, dict(data, starts='08:45', ends='09:00')).status_code, 201)
        self.assertEqual(self.client.post(url, dict(data, starts='10:00')).status_code, 400)
        for user, count in [(self.teacher.user, 2), (self.student, 2), (self.other, 0)]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(url).data['count'], count)
            self.assertEqual(sum(v['total'] for v in self.client.get(url+'distribution/').data), count)
            self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(self.client.get(url+str(created.data['id'])+'/').status_code, 404)

    def test_resources_and_notices_are_read_only_for_non_admins(self):
        for key, data in [('notices', {'title':'Assembly', 'message':'Meet at 9.'}),
                          ('library', {'title':'Reading', 'subject':self.subject.pk, 'url':'https://example.org/book'})]:
            url = '/api/v1/'+key+'/'
            self.client.force_authenticate(self.admin)
            item = self.client.post(url, data)
            self.assertEqual(item.status_code, 201, item.data)
            detail = url+str(item.data['id'])+'/'
            for user in [self.student, self.teacher.user]:
                self.client.force_authenticate(user)
                self.assertEqual(self.client.get(detail).status_code, 200)
                self.assertEqual(self.client.patch(detail, {'title':'Changed'}).status_code, 403)
                self.assertEqual(self.client.delete(detail).status_code, 403)
            self.client.force_authenticate(None)
            self.assertEqual(self.client.get(detail).status_code, 401)

    def test_dashboard_activity_uses_role_scope(self):
        from django.utils import timezone
        from attendance.models import Attendance
        from scores.models import Score

        pupil = self.student.student_profile
        Attendance.objects.create(student=pupil, class_obj=self.cls, status='present', date=timezone.localdate())
        Score.objects.create(student=pupil, subject=self.subject, class_subject=self.assignment,
                             assessment_type='test', marks_obtained=85, max_marks=100)
        for user, visible in [(self.admin, 1), (self.teacher.user, 1), (self.student, 1), (self.other, 0)]:
            self.client.force_authenticate(user)
            response = self.client.get('/api/v1/dashboard-activity/')
            self.assertEqual(len(response.data['scores']), visible)
            self.assertEqual(sum(row['total'] for row in response.data['attendance']), visible)
