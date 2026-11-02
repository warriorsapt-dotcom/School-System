# School Management Platform - Django Implementation

A complete, production-ready Django REST API for managing a comprehensive school system with student records, attendance tracking, academic performance monitoring, and progress analytics.

## 📋 Quick Links

- [Setup Guide](SETUP_GUIDE.md) - Complete installation instructions
- [Project Summary](PROJECT_SUMMARY.md) - Overview and implementation checklist
- [API Documentation](#api-endpoints) - Full API endpoint reference

## 🎯 Project Highlights

- ✅ **Complete Database Schema** - Comprehensive PostgreSQL setup with all relationships
- ✅ **Django Models** - All models with proper relationships and validations
- ✅ **REST API** - Full CRUD operations with viewsets and custom actions
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **Role-Based Access Control** - Admin, Teacher, Student permissions
- ✅ **Attendance System** - Daily tracking with summaries
- ✅ **Scoring System** - Assessment recording with teacher comments
- ✅ **Results Calculation** - Automatic term and yearly result generation
- ✅ **Progress Tracking** - Historical data and trend analysis
- ✅ **Image Management** - Admin photo uploads with categories

## 📁 Project Files Provided

### Database
| File | Purpose |
|------|---------|
| `postgres_setup.sql` | Complete PostgreSQL schema, tables, indexes, and triggers |

### Configuration
| File | Purpose |
|------|---------|
| `settings.py` | Django settings with PostgreSQL, JWT, CORS configuration |
| `.env.example` | Environment variables template (copy to .env) |
| `requirements.txt` | All Python dependencies |

### Django Models
| File | Models Included |
|------|-----------------|
| `users_models.py` | CustomUser, Teacher, Student, Admin, SchoolImage |
| `classes_models.py` | Class, Subject, ClassSubject, Term |
| `attendance_models.py` | Attendance, AttendanceSummary |
| `scores_results_models.py` | Score, ScoreComment, SubjectPerformance, TermResult, YearlyResult, ProgressLog |

### API Layer
| File | Purpose |
|------|---------|
| `serializers_example.py` | DRF serializers for all models and operations |
| `views_example.py` | API ViewSets, Views, and custom actions |
| `urls_example.py` | URL routing configuration with REST endpoints |

### Utilities & Setup
| File | Purpose |
|------|---------|
| `utils_and_commands.py` | Calculation functions and management commands |
| `setup.sh` | Automated project initialization script |

### Documentation
| File | Purpose |
|------|---------|
| `SETUP_GUIDE.md` | Step-by-step installation and configuration |
| `PROJECT_SUMMARY.md` | Complete project overview and implementation checklist |
| `README.md` | This file - quick reference |

## 🚀 Quick Start (5 Minutes)

### Prerequisites
```bash
# Install PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql
# Windows: Download from https://www.postgresql.org/download/windows/

# Install Python 3.8+
# Check: python3 --version
```

### Setup Steps
```bash
# 1. Clone/create project and navigate to it
cd school_management_platform

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Run automated setup (creates DB and runs migrations)
chmod +x setup.sh
./setup.sh

# 6. Create admin user
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver
```

Access:
- Admin Panel: http://localhost:8000/admin/
- API: http://localhost:8000/api/v1/

## 🔐 Authentication

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@school.com", "password": "password"}'
```

Response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {...}
}
```

### Use Token
```bash
curl -X GET http://localhost:8000/api/v1/users/students/ \
  -H "Authorization: Bearer <access_token>"
```

## 📚 API Endpoints

### Authentication
```
POST   /api/v1/auth/register/              Register new user
POST   /api/v1/auth/login/                 Login and get tokens
POST   /api/v1/auth/logout/                Logout
POST   /api/v1/auth/change-password/       Change password
GET    /api/v1/auth/profile/               Get profile
PUT    /api/v1/auth/profile/               Update profile
```

### Teachers & Students
```
GET    /api/v1/users/teachers/             List all teachers
GET    /api/v1/users/teachers/{id}/        Get teacher details
GET    /api/v1/users/teachers/{id}/classes/     Get teacher's classes
GET    /api/v1/users/teachers/{id}/subjects/    Get teacher's subjects

GET    /api/v1/users/students/             List all students
GET    /api/v1/users/students/{id}/        Get student details
GET    /api/v1/users/students/{id}/results/    Get student results
GET    /api/v1/users/students/{id}/progress/   Get progress data
```

### Classes & Subjects
```
GET    /api/v1/classes/                    List all classes
GET    /api/v1/classes/{id}/               Get class details
GET    /api/v1/classes/{id}/students/      Get students in class
GET    /api/v1/classes/{id}/attendance/    Get class attendance

GET    /api/v1/subjects/                   List all subjects
GET    /api/v1/terms/                      List academic terms
```

### Attendance
```
POST   /api/v1/attendance/                 Mark attendance
GET    /api/v1/attendance/                 Get attendance records
GET    /api/v1/attendance/summary/         Get attendance summary
POST   /api/v1/attendance/bulk_mark/       Bulk mark attendance
```

### Scores & Results
```
POST   /api/v1/scores/                     Record score
GET    /api/v1/scores/                     Get all scores
GET    /api/v1/scores/student_scores/      Get student scores
POST   /api/v1/scores/{id}/add_comment/    Add comment to score

GET    /api/v1/results/                    Get term results
GET    /api/v1/results/class_ranking/      Get class rankings
GET    /api/v1/progress/chart/             Get progress chart data
```

### Image Management
```
POST   /api/v1/images/                     Upload image (Admin)
GET    /api/v1/images/                     List images
DELETE /api/v1/images/{id}/                Delete image (Admin)
```

## 👥 User Roles & Permissions

### Admin
- Create/manage users (teachers, students)
- Manage academic calendar (classes, terms)
- Upload school images
- View all data and reports
- Approve results

### Teacher
- View their assigned class
- Mark attendance
- Record scores
- Comment on student performance
- View class summaries

### Student
- View personal attendance
- View personal scores
- View results
- Track progress
- View profile

## 📊 Database Schema Overview

### Core Tables
```
CustomUser (Authentication)
├── Teacher (1-to-1)
├── Student (1-to-1)
├── Admin (1-to-1)
└── SchoolImage

Class (Academic Structure)
├── Students (1-to-many)
├── ClassSubject (1-to-many)
└── Attendance (1-to-many)

Subject
└── ClassSubject

Term (Academic Calendar)
├── Attendance (1-to-many)
├── Score (1-to-many)
└── TermResult (1-to-many)

Score (Assessment)
├── ScoreComment (1-to-many)
└── SubjectPerformance

Result Models
├── TermResult (Term-level)
├── YearlyResult (Year-level)
└── ProgressLog (Historical)
```

## 🔧 Django Apps Structure

```
school_platform/
├── users/                 # Authentication & profiles
│   ├── models.py         # CustomUser, Teacher, Student
│   ├── views.py          # User viewsets
│   ├── serializers.py    # User serializers
│   └── urls.py           # User endpoints
│
├── classes/              # Academic structure
│   ├── models.py         # Class, Subject, Term
│   ├── views.py          # Class viewsets
│   └── serializers.py
│
├── attendance/           # Attendance system
│   ├── models.py         # Attendance models
│   ├── views.py          # Attendance viewsets
│   └── serializers.py
│
├── scores/              # Academic performance
│   ├── models.py         # Score, Result models
│   ├── views.py          # Result viewsets
│   ├── serializers.py
│   └── management/       # Custom commands
│
├── settings.py          # Main configuration
├── urls.py              # Main routing
└── wsgi.py              # Deployment
```

## 📝 Common Tasks

### Create Sample Data
```bash
python manage.py shell
```

In Python shell:
```python
from classes.models import Subject, Term
from datetime import date

# Create subjects
subjects = ['English', 'Mathematics', 'Science', 'History', 'Geography']
for name in subjects:
    Subject.objects.get_or_create(name=name)

# Create current term
Term.objects.get_or_create(
    name='first',
    academic_year='2024/2025',
    defaults={
        'start_date': date(2024, 1, 15),
        'end_date': date(2024, 4, 15),
        'is_current': True
    }
)
```

### Generate Results for Class
```bash
python manage.py generate_term_results --term first --class "Form 1A"
```

### Bulk Mark Attendance
```bash
curl -X POST http://localhost:8000/api/v1/attendance/bulk_mark/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "attendances": [
      {"student": "<id>", "status": "present", "date": "2024-01-15"},
      {"student": "<id>", "status": "absent", "date": "2024-01-15"}
    ]
  }'
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📦 Deployment Checklist

- [ ] Change SECRET_KEY in settings.py
- [ ] Set DEBUG = False
- [ ] Configure allowed hosts
- [ ] Set up PostgreSQL on server
- [ ] Configure email settings
- [ ] Set up static files with S3 or similar
- [ ] Enable HTTPS
- [ ] Configure CORS for frontend domain
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Use environment variables for sensitive data
- [ ] Test all API endpoints
- [ ] Set up CI/CD pipeline

## 🛠️ Troubleshooting

### Issue: "psycopg2 error: connection refused"
```bash
# Check PostgreSQL is running
# macOS: brew services start postgresql
# Ubuntu: sudo systemctl start postgresql

# Verify connection settings in .env
```

### Issue: "ModuleNotFoundError: No module named 'django'"
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: "JWT token expired"
```bash
# Use refresh endpoint to get new token
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)

## 📞 Support

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)
For project overview, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## 📄 License

This project is provided as-is for educational and commercial use.

## ✅ Checklist Before Going Live

- [ ] Database configured and backed up
- [ ] All models created and migrated
- [ ] API endpoints tested
- [ ] Authentication working
- [ ] User roles and permissions working
- [ ] Attendance system tested
- [ ] Scoring system tested
- [ ] Results calculation working
- [ ] Frontend integrated
- [ ] Email notifications configured
- [ ] Security audit completed
- [ ] Performance optimized
- [ ] Monitoring set up
- [ ] Documentation complete

---

**Version**: 1.0
**Last Updated**: 2024
**Status**: Ready for Production Implementation

For questions or issues, refer to the included documentation files.
