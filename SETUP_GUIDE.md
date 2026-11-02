# Django School Platform - Setup Guide

This is a comprehensive guide to set up the school management platform using Django, PostgreSQL, and DRF.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git
- Virtual Environment (venv)
- pip (Python package manager)

## Project Structure

```
school_platform/
├── school_platform/              # Main project settings
│   ├── __init__.py
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Project URL routing
│   ├── asgi.py
│   └── wsgi.py
├── users/                        # User authentication app
│   ├── migrations/
│   ├── models.py               # CustomUser, Teacher, Student, Admin models
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
├── classes/                      # Classes and subjects app
│   ├── migrations/
│   ├── models.py               # Class, Subject, ClassSubject, Term
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── attendance/                   # Attendance tracking app
│   ├── migrations/
│   ├── models.py               # Attendance, AttendanceSummary
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── scores/                       # Scores and results app
│   ├── migrations/
│   ├── models.py               # Score, ScoreComment, Results
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── manage.py
├── requirements.txt
├── .env
└── README.md
```

## Step-by-Step Installation

### 1. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install PostgreSQL

#### On Windows:
- Download from: https://www.postgresql.org/download/windows/
- Run the installer
- Note the password you set for the postgres user
- Add PostgreSQL to your PATH

#### On macOS:
```bash
brew install postgresql@15
brew services start postgresql@15
```

#### On Ubuntu/Debian:
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 3. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql shell:
CREATE DATABASE school_platform;
CREATE USER school_user WITH PASSWORD 'your_secure_password';
ALTER ROLE school_user SET client_encoding TO 'utf8';
ALTER ROLE school_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE school_user SET default_transaction_deferrable TO on;
ALTER ROLE school_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE school_platform TO school_user;
\q
```

### 4. Clone/Create Django Project

```bash
# Create project directory
mkdir school_management_platform
cd school_management_platform

# Initialize git (optional)
git init

# Create Django project structure (if starting fresh)
django-admin startproject school_platform .
django-admin startapp users
django-admin startapp classes
django-admin startapp attendance
django-admin startapp scores
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env with your configuration
# Update database credentials, secret key, email settings, etc.
```

### 7. Create and Apply Migrations

```bash
# Create migrations for all apps
python manage.py makemigrations users classes attendance scores

# Apply migrations
python manage.py migrate
```

### 8. Create Superuser (Admin)

```bash
python manage.py createsuperuser
# Follow the prompts to create admin account
```

### 9. Create Initial Data (Optional)

```bash
python manage.py shell
```

In the Django shell:
```python
from users.models import CustomUser, Admin
from classes.models import Subject, Term
from datetime import date, timedelta

# Create some subjects
subjects_data = [
    {'name': 'English', 'code': 'ENG101'},
    {'name': 'Mathematics', 'code': 'MAT101'},
    {'name': 'Science', 'code': 'SCI101'},
    {'name': 'History', 'code': 'HIS101'},
    {'name': 'Geography', 'code': 'GEO101'},
]

for subject in subjects_data:
    Subject.objects.get_or_create(**subject)

# Create academic terms
terms_data = [
    {
        'name': 'first',
        'academic_year': '2024/2025',
        'start_date': date(2024, 1, 15),
        'end_date': date(2024, 4, 15),
        'is_current': True
    },
    {
        'name': 'second',
        'academic_year': '2024/2025',
        'start_date': date(2024, 4, 22),
        'end_date': date(2024, 8, 15),
    },
    {
        'name': 'third',
        'academic_year': '2024/2025',
        'start_date': date(2024, 9, 2),
        'end_date': date(2024, 11, 29),
    },
]

for term_data in terms_data:
    Term.objects.get_or_create(**term_data)

print("Initial data created successfully!")
exit()
```

### 10. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 11. Run Development Server

```bash
python manage.py runserver
```

The application will be available at: `http://127.0.0.1:8000/`
Admin panel: `http://127.0.0.1:8000/admin/`

## API Endpoints Structure

### Authentication
```
POST   /api/auth/register/          - Register new user
POST   /api/auth/login/             - Login user
POST   /api/auth/logout/            - Logout user
POST   /api/auth/refresh/           - Refresh JWT token
GET    /api/auth/profile/           - Get current user profile
```

### Users (Teachers, Students)
```
GET    /api/users/teachers/         - List all teachers
GET    /api/users/teachers/<id>/    - Get teacher details
GET    /api/users/students/         - List all students
GET    /api/users/students/<id>/    - Get student details
POST   /api/users/students/         - Create new student (Admin)
PUT    /api/users/students/<id>/    - Update student profile
```

### Classes & Subjects
```
GET    /api/classes/                - List all classes
GET    /api/classes/<id>/           - Get class details
GET    /api/classes/<id>/students/  - Get students in class
GET    /api/subjects/               - List all subjects
GET    /api/classes/<id>/subjects/  - Get subjects for a class
```

### Attendance
```
POST   /api/attendance/             - Mark attendance
GET    /api/attendance/             - Get attendance records
GET    /api/attendance/summary/     - Get attendance summary
GET    /api/attendance/student/<id>/- Get student attendance
```

### Scores & Results
```
POST   /api/scores/                 - Record score
GET    /api/scores/                 - Get all scores
GET    /api/scores/student/<id>/    - Get student scores
POST   /api/scores/<id>/comments/   - Add comment to score
GET    /api/results/term/           - Get term results
GET    /api/results/yearly/         - Get yearly results
GET    /api/progress/<student_id>/  - Get student progress chart data
```

### Images (Admin)
```
POST   /api/images/                 - Upload school image
GET    /api/images/                 - Get all images
GET    /api/images/?category=school - Get images by category
DELETE /api/images/<id>/            - Delete image
```

## Database Schema Overview

### Core Tables
- **users** - Custom user accounts (Admin, Teacher, Student)
- **classes** - School classes/forms
- **subjects** - Academic subjects
- **class_subjects** - Relationship between classes and subjects with assigned teacher

### Student Management
- **students** - Student profile information
- **attendance** - Attendance records
- **attendance_summary** - Monthly/term attendance summary

### Academic Performance
- **scores** - Individual assessment marks
- **score_comments** - Teacher feedback on scores
- **subject_performance** - Summary of performance per subject per term
- **term_results** - Complete results for a term
- **yearly_results** - Annual summary
- **progress_log** - Historical progress tracking

### Admin Management
- **teachers** - Teacher profile information
- **school_images** - Images uploaded by administrators

## User Roles and Permissions

### Admin
- Manage users (create teachers, students)
- Upload school images
- View all results and attendance
- Manage academic calendar (terms, classes)
- Generate reports

### Teacher
- Mark attendance for their class
- Record scores and marks
- Comment on student performance
- View class attendance summary
- Access their assigned class information

### Student
- View personal attendance
- View personal scores and results
- Track progress over terms
- View term and yearly results
- Access progress charts

## Authentication

The system uses JWT (JSON Web Tokens) for API authentication:

1. User logs in with credentials
2. Receives access and refresh tokens
3. Access token valid for 1 hour
4. Refresh token valid for 7 days
5. Include access token in Authorization header for API requests

```
Authorization: Bearer <access_token>
```

## Important Notes

### Security
- Change SECRET_KEY in production
- Set DEBUG = False in production
- Use environment variables for sensitive data
- Use HTTPS in production
- Configure CSRF and CORS properly

### Database
- Always backup your database
- Use connection pooling in production
- Monitor database performance
- Create regular backups

### File Uploads
- Store images securely
- Use S3 or similar cloud storage in production
- Implement file size limits
- Validate file types

### Performance
- Use caching for frequently accessed data
- Add database indexes (included in models)
- Monitor API response times
- Use pagination for large datasets

## Testing

```bash
# Run tests
python manage.py test

# Run tests for specific app
python manage.py test users

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
# Verify connection settings in .env
# Test connection: psql -U school_user -d school_platform
```

### Migration Errors
```bash
# Clear migrations and start fresh (CAREFUL - deletes data)
python manage.py migrate classes zero
python manage.py migrate

# Or create fresh migrations
python manage.py makemigrations --empty classes --name fix_issue
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python path
echo $PYTHONPATH
```

## Next Steps

1. Create Frontend (React, Vue, or Angular)
2. Set up automated testing
3. Configure email notifications
4. Add dashboard with charts
5. Implement PDF report generation
6. Set up background tasks (Celery)
7. Deploy to production (Heroku, AWS, DigitalOcean)

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- JWT Authentication: https://django-rest-framework-simplejwt.readthedocs.io/

## Support

For issues or questions:
1. Check error messages carefully
2. Review the Django logs
3. Check database queries
4. Test API endpoints with Postman/Insomnia
5. Enable DEBUG mode for detailed error information

---

Created: 2024
Last Updated: 2024
