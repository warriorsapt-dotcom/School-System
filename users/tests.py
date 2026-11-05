from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class ProfileProvisioningTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email='head@example.com', username='head', password='TestPass123!')
        self.client.force_login(self.admin)

    def test_admin_profile_add_sets_access_on_first_login(self):
        from classes.models import Class
        school_class = Class.objects.create(name='Form 1', form_level=1)
        cases = [
            ('teacher', 'student', {'employee_id': 'T1'}),
            ('student', 'teacher', {'admission_number': 'S1', 'class_assigned': school_class.pk}),
        ]
        for role, initial_role, fields in cases:
            with self.subTest(role=role):
                account = User.objects.create_user(email=f'{role}@example.com', username=role,
                                                   role=initial_role, password='TestPass123!')
                response = self.client.post(f'/admin/users/{role}/add/', {
                    'user': account.pk, 'is_active': 'on', **fields,
                })
                self.assertEqual(response.status_code, 302)
                login = self.client.post('/api/v1/auth/login/', {'email': account.email, 'password': 'TestPass123!'})
                self.assertEqual(login.data['user']['role'], role)
                self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login.data['access'])
                profile = getattr(account, f'{role}_profile')
                url = f'/api/v1/users/{role}s/{profile.pk}/'
                self.assertEqual(self.client.get(url).status_code, 200)
                self.assertEqual(self.client.patch(url, {'is_active': False}).status_code, 403)
                self.client.credentials()

    def test_privileged_account_cannot_be_linked_to_school_profile(self):
        response = self.client.post('/admin/users/teacher/add/', {'user': self.admin.pk, 'employee_id': 'T1'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.context['adminform'].form.errors)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, 'admin')


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@school.com',
            username='test@school.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
            role='admin',
        )

    def test_login_success(self):
        res = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'test@school.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertIn('user', res.data)

    def test_login_wrong_password(self):
        res = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'test@school.com', 'password': 'wrongpass'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials(self):
        res = self.client.post('/api/v1/auth/login/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_requires_auth(self):
        res = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_with_auth(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'test@school.com')

    def test_student_list_requires_auth(self):
        res = self.client.get('/api/v1/users/students/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SchoolSettingsTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        from users.models import SchoolConfiguration
        cache.clear()
        self.config = SchoolConfiguration.objects.create(school_name='Kahuho Secondary School', account_suffix='ksc')
        self.admin = User.objects.create_superuser(email='admin@example.com', username='admin', password='TestPass123!')
        self.student = User.objects.create_user(email='student@example.com', username='student', password='TestPass123!', role='student')

    def test_only_admin_can_change_settings(self):
        url = '/api/v1/school-settings/'
        self.assertEqual(self.client.get(url).data['account_suffix'], 'ksc')
        self.assertEqual(self.client.patch(url, {'account_suffix': 'ktp'}).status_code, 401)
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.patch(url, {'account_suffix': 'ktp'}).status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(url, {'school_name': 'Kiambogo Township Primary', 'account_suffix': ' KTP '})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['account_suffix'], 'ktp')
        self.config.refresh_from_db()
        self.assertEqual(self.config.school_name, 'Kiambogo Township Primary')

    def test_invalid_settings_are_rejected(self):
        self.client.force_authenticate(self.admin)
        for suffix in ['@ksc', 'bad suffix', '<script>', 'ksc/', 'a..b', '-ksc', '']:
            with self.subTest(suffix=suffix):
                self.assertEqual(self.client.patch('/api/v1/school-settings/', {'account_suffix': suffix}).status_code, 400)
        self.assertEqual(self.client.patch('/api/v1/school-settings/', {'school_name': '  '}).status_code, 400)

    def test_teacher_creation_and_login_with_school_id(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/v1/users/teachers/', {'email': 'mary', 'employee_id': 'T99', 'password': 'TestPass123!', 'first_name': 'Mary'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['user']['email'], 'mary@ksc')
        self.client.force_authenticate(None)
        for login in ['mary@ksc', 'mary']:
            response = self.client.post('/api/v1/auth/login/', {'email': login, 'password': 'TestPass123!'}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
        self.config.account_suffix = 'ktp'
        self.config.save()
        response = self.client.post('/api/v1/auth/login/', {'email': 'mary@ksc', 'password': 'TestPass123!'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)

    def test_students_use_new_suffix_and_duplicates_are_rejected(self):
        self.config.account_suffix = 'ktp'
        self.config.save()
        self.client.force_authenticate(self.admin)
        payload = {'email': 'peter', 'admission_number': 'A99', 'password': 'TestPass123!'}
        response = self.client.post('/api/v1/users/students/', payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['user']['email'], 'peter@ktp')
        payload['admission_number'] = 'A100'
        response = self.client.post('/api/v1/users/students/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_invalid_login_ids_return_validation_errors(self):
        self.client.force_authenticate(self.admin)
        for email in ['mary@@ksc', 'mary smith', '<script>@ksc', '.mary@ksc']:
            response = self.client.post('/api/v1/users/teachers/', {'email': email, 'employee_id': 'T99'}, format='json')
            self.assertEqual(response.status_code, 400, response.data)

    def test_profile_cannot_grant_school_settings_access(self):
        self.client.force_authenticate(self.student)
        self.client.put('/api/v1/auth/profile/', {'role': 'admin'}, format='json')
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, 'student')
        self.assertEqual(self.client.patch('/api/v1/school-settings/', {'account_suffix': 'evil'}).status_code, 403)

    def test_public_registration_cannot_create_admin(self):
        response = self.client.post('/api/v1/auth/register/', {'email': 'rogue@ksc', 'username': 'rogue', 'password': 'TestPass123!', 'password_confirm': 'TestPass123!', 'role': 'admin'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='rogue').exists())

    def test_pages_show_school_branding_safely(self):
        response = self.client.get('/')
        self.assertContains(response, 'Kahuho Secondary School')
        self.assertContains(response, 'you@ksc')
        self.config.school_name = '<script>alert(1)</script>'
        self.config.save()
        response = self.client.get('/dashboard/')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_admin_form_accepts_internal_id(self):
        from django.forms import modelform_factory
        Form = modelform_factory(User, fields=['email'])
        form = Form(data={'email': 'head@ksc'})
        self.assertTrue(form.is_valid(), form.errors)
