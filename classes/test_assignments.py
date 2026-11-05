from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APITestCase

from classes.models import Class
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
        data = {'class_obj':str(self.cls.pk), 'title':'Homework'}
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
