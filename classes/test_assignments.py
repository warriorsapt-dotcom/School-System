from io import BytesIO
from zipfile import ZipFile
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from classes.models import Assignment, Class
from users.models import Student, Teacher


class AssignmentTests(APITestCase):
    url = '/api/v1/assignments/'

    def setUp(self):
        def account(name, role):
            return get_user_model().objects.create_user(email=name+'@school.test', username=name, role=role)
        self.teacher = Teacher.objects.create(user=account('teacher','teacher'), employee_id='T1')
        self.cls = Class.objects.create(name='Form A', form_level=1, class_teacher=self.teacher)
        self.other_class = Class.objects.create(name='Form B', form_level=1)
        self.student = Student.objects.create(user=account('student','student'), class_assigned=self.cls, admission_number='A1')
        self.other = Student.objects.create(user=account('other','student'), class_assigned=self.other_class, admission_number='B1')
        self.client.force_authenticate(self.teacher.user)

    def post(self, **fields):
        data = {'class_obj':str(self.cls.pk), 'title':'Homework',
                'deadline': (timezone.now() + timedelta(days=1)).isoformat()}
        data.update(fields)
        return self.client.post(self.url,data,format='multipart')

    def test_file_only_uploads(self):
        word = BytesIO()
        with ZipFile(word,'w') as archive:
            archive.writestr('word/document.xml','<document/>')
            archive.writestr('[Content_Types].xml','<Types/>')
        png = BytesIO()
        Image.new('RGB',(2,2)).save(png,'PNG')
        for name, payload in [('work.docx',word.getvalue()),('work.png',png.getvalue()),('work.pdf',b'%PDF-1.4\n%%EOF')]:
            with self.subTest(name=name):
                response = self.post(file=SimpleUploadedFile(name,payload))
                self.assertEqual(response.status_code,201,response.data)
                self.assertEqual(response.data['filename'],name)
                self.client.force_authenticate(self.student.user)
                download = self.client.get(self.url+str(response.data['id'])+'/download/')
                self.assertEqual(b''.join(download.streaming_content),payload)
                self.client.force_authenticate(self.teacher.user)

    def test_class_scope_and_writes(self):
        response = self.post(instructions='Read chapter one.')
        self.assertEqual(response.status_code,201)
        self.assertEqual(self.post(class_obj=str(self.other_class.pk),instructions='Hello').status_code,400)
        self.client.force_authenticate(self.other.user)
        self.assertEqual(self.client.get(self.url).data['count'],0)
        self.assertEqual(self.client.get(self.url+str(response.data['id'])+'/download/').status_code,404)
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self.client.get(self.url).data['count'],1)
        self.assertEqual(self.post(instructions='Hello').status_code,403)

    def test_invalid_uploads_and_empty_assignments(self):
        self.assertEqual(self.post().status_code,400)
        for name in ['bad.docx','bad.png','bad.exe','bad.pdf']:
            self.assertEqual(self.post(file=SimpleUploadedFile(name,b'invalid')).status_code,400)
        self.assertEqual(self.post(file=SimpleUploadedFile('large.pdf',b'%PDF-'+bytes(10*1024*1024))).status_code,400)

    def test_deadline_required_and_must_be_future(self):
        response = self.client.post(self.url, {'class_obj':str(self.cls.pk), 'title':'Work', 'instructions':'Read.'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('deadline', response.data)
        self.assertEqual(self.post(instructions='Read.', deadline=(timezone.now()-timedelta(seconds=1)).isoformat()).status_code, 400)

    def test_expiry_hides_list_detail_and_download_but_preserves_teacher_copy(self):
        deadline = timezone.now() + timedelta(hours=1)
        response = self.post(deadline=deadline.isoformat(), file=SimpleUploadedFile('work.pdf', b'%PDF-1.4\n%%EOF'))
        self.assertEqual(response.status_code, 201)
        detail = self.url + str(response.data['id']) + '/'
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self.client.get(self.url).data['count'], 1)
        with patch('classes.assignments.timezone.now', return_value=deadline):
            self.assertEqual(self.client.get(self.url).data['count'], 0)
            self.assertEqual(self.client.get(detail).status_code, 404)
            self.assertEqual(self.client.get(detail+'download/').status_code, 404)
            self.client.force_authenticate(self.teacher.user)
            self.assertEqual(self.client.get(self.url).data['count'], 1)
            self.assertEqual(self.client.get(detail).status_code, 200)
            self.assertEqual(self.client.get(detail+'download/').status_code, 200)
        self.assertTrue(Assignment.objects.filter(pk=response.data['id']).exists())

    def test_existing_assignments_without_deadline_remain_visible(self):
        Assignment.objects.create(title='Existing work', instructions='Read.', class_obj=self.cls, teacher=self.teacher)
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self.client.get(self.url).data['count'], 1)
