# Project Folder Structure & Implementation Guide

## 📁 Complete Directory Layout

```
school_management_platform/          # Project root
│
├── venv/                            # Virtual environment (created during setup)
│
├── school_platform/                 # Main Django project folder
│   ├── __init__.py
│   ├── settings.py                  # 📌 Copy from provided settings.py
│   ├── urls.py                      # 📌 Copy from provided urls_example.py
│   ├── asgi.py                      # Auto-generated
│   └── wsgi.py                      # Auto-generated
│
├── users/                           # Users app
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── management/
│   │   └── commands/
│   ├── __init__.py
│   ├── models.py                    # 📌 Copy from provided users_models.py
│   ├── views.py                     # 📌 Copy from provided views_example.py
│   ├── serializers.py               # 📌 Copy from provided serializers_example.py
│   ├── urls.py
│   ├── tests.py
│   ├── apps.py
│   └── admin.py
│
├── classes/                         # Classes app
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── __init__.py
│   ├── models.py                    # 📌 Copy from provided classes_models.py
│   ├── views.py                     # 📌 Copy from provided views_example.py
│   ├── serializers.py               # 📌 Copy from provided serializers_example.py
│   ├── urls.py
│   ├── tests.py
│   ├── apps.py
│   └── admin.py
│
├── attendance/                      # Attendance app
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── __init__.py
│   ├── models.py                    # 📌 Copy from provided attendance_models.py
│   ├── views.py                     # 📌 Copy from provided views_example.py
│   ├── serializers.py               # 📌 Copy from provided serializers_example.py
│   ├── urls.py
│   ├── tests.py
│   ├── apps.py
│   └── admin.py
│
├── scores/                          # Scores & Results app
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── generate_term_results.py
│   │       ├── create_academic_year.py
│   │       └── cleanup_old_data.py
│   ├── __init__.py
│   ├── models.py                    # 📌 Copy from provided scores_results_models.py
│   ├── views.py                     # 📌 Copy from provided views_example.py
│   ├── serializers.py               # 📌 Copy from provided serializers_example.py
│   ├── urls.py
│   ├── tests.py
│   ├── apps.py
│   ├── admin.py
│   └── utils.py                     # 📌 Copy from provided utils_and_commands.py
│
├── templates/                       # Django templates (for admin/optional)
│   └── base.html
│
├── static/                          # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│
├── staticfiles/                     # Collected static files (auto-generated)
│
├── media/                           # User uploads
│   ├── profile_pictures/
│   ├── school_images/
│   │   └── 2024/01/15/
│   └── documents/
│
├── logs/                            # Application logs
│   └── debug.log
│
├── manage.py                        # Django management script (auto-generated)
├── requirements.txt                 # 📌 Provided
├── .env                             # 📌 Copy from .env.example and configure
├── .env.example                     # 📌 Provided
├── .gitignore                       # For version control
├── setup.sh                         # 📌 Provided - automated setup
│
└── docs/                            # Documentation (optional)
    ├── README.md                    # 📌 Provided
    ├── SETUP_GUIDE.md              # 📌 Provided
    └── PROJECT_SUMMARY.md          # 📌 Provided
```

📌 = File provided in the output package

## 🎯 Step-by-Step Implementation

### Phase 1: Project Setup (30 minutes)

#### Step 1.1: Create Project Structure
```bash
# Create project directory
mkdir school_management_platform
cd school_management_platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create Django project
django-admin startproject school_platform .
```

#### Step 1.2: Create Apps
```bash
# Create all apps
python manage.py startapp users
python manage.py startapp classes
python manage.py startapp attendance
python manage.py startapp scores
```

#### Step 1.3: Configure Files
```bash
# Copy provided files
cp /path/to/settings.py school_platform/settings.py
cp /path/to/requirements.txt .
cp /path/to/.env.example .env

# Edit .env with your database credentials
# Install dependencies
pip install -r requirements.txt
```

#### Step 1.4: Set Up Database
```bash
# Create PostgreSQL database (as shown in postgres_setup.sql)
createdb school_platform
createuser school_user

# Create .env with database credentials
# DB_NAME=school_platform
# DB_USER=school_user
# DB_PASSWORD=your_password
# DB_HOST=localhost
```

---

### Phase 2: Models Implementation (1-2 hours)

#### Step 2.1: Copy Model Files

Copy the provided model files to each app:

**users/models.py**
```bash
# Copy from: provided users_models.py
```

**classes/models.py**
```bash
# Copy from: provided classes_models.py
```

**attendance/models.py**
```bash
# Copy from: provided attendance_models.py
```

**scores/models.py**
```bash
# Copy from: provided scores_results_models.py
```

#### Step 2.2: Register Models in Admin

Edit each app's `admin.py`:
```python
from django.contrib import admin
from .models import *

# Register all models
# Example:
admin.site.register(CustomUser)
admin.site.register(Teacher)
admin.site.register(Student)
# ... etc
```

#### Step 2.3: Create Migrations
```bash
python manage.py makemigrations users
python manage.py makemigrations classes
python manage.py makemigrations attendance
python manage.py makemigrations scores
python manage.py migrate
```

#### Step 2.4: Verify Models
```bash
python manage.py shell
# Test importing models
from users.models import CustomUser
from classes.models import Class
# etc
```

---

### Phase 3: Serializers Implementation (1 hour)

#### Step 3.1: Create Serializers Files
```bash
# Create serializers.py in each app
touch users/serializers.py
touch classes/serializers.py
touch attendance/serializers.py
touch scores/serializers.py
```

#### Step 3.2: Copy Serializer Code
Copy relevant serializers from provided `serializers_example.py` to each app's `serializers.py`

#### Step 3.3: Test Serializers
```bash
python manage.py shell
from users.serializers import CustomUserSerializer
# Test serialization
```

---

### Phase 4: Views/ViewSets Implementation (1-2 hours)

#### Step 4.1: Create Views Files
```bash
# Create views.py (already exists, just edit)
# Copy from provided views_example.py
```

#### Step 4.2: Set Up URL Routing

Create `urls.py` in each app and main `urls.py`:

**school_platform/urls.py** - Copy from provided `urls_example.py`

**users/urls.py**
```python
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, StudentViewSet

router = DefaultRouter()
router.register(r'teachers', TeacherViewSet)
router.register(r'students', StudentViewSet)

urlpatterns = router.urls
```

Repeat for other apps.

#### Step 4.3: Test API Endpoints
```bash
python manage.py runserver
# Visit: http://localhost:8000/api/v1/
# Try endpoints in browser or with curl
```

---

### Phase 5: Utility Functions & Commands (1 hour)

#### Step 5.1: Create Utilities
```bash
# Create in scores app
touch scores/utils.py
# Copy from: provided utils_and_commands.py
```

#### Step 5.2: Create Management Commands
```bash
# Create directory structure
mkdir -p scores/management/commands
touch scores/management/__init__.py
touch scores/management/commands/__init__.py

# Create command files
touch scores/management/commands/generate_term_results.py
touch classes/management/commands/create_academic_year.py

# Copy command implementations from utils_and_commands.py
```

#### Step 5.3: Test Commands
```bash
python manage.py create_academic_year --year 2024/2025
python manage.py generate_term_results --term first --class "Form 1A"
```

---

### Phase 6: Testing & Initial Data (1 hour)

#### Step 6.1: Create Initial Data
```bash
python manage.py shell < seed_data.py
```

Or manually:
```bash
python manage.py shell

# Create admin
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin@school.com', 'admin', 'admin@123')

# Create subjects
from classes.models import Subject
subjects = ['English', 'Maths', 'Science', 'History', 'Geography']
for name in subjects:
    Subject.objects.create(name=name)

# Create terms
from classes.models import Term
from datetime import date
Term.objects.create(
    name='first',
    academic_year='2024/2025',
    start_date=date(2024, 1, 15),
    end_date=date(2024, 4, 15),
    is_current=True
)
```

#### Step 6.2: Test in Admin
```bash
python manage.py runserver
# Visit: http://localhost:8000/admin/
# Login with created superuser
# Verify models appear
```

#### Step 6.3: Run Basic Tests
```bash
python manage.py test
```

---

## 📋 File Mapping Guide

Here's which provided file goes where:

| Source File | Destination |
|------------|-------------|
| postgres_setup.sql | Run in PostgreSQL (initial database setup) |
| settings.py | `school_platform/settings.py` |
| users_models.py | `users/models.py` |
| classes_models.py | `classes/models.py` |
| attendance_models.py | `attendance/models.py` |
| scores_results_models.py | `scores/models.py` |
| serializers_example.py | Distribute to each app's `serializers.py` |
| views_example.py | Distribute to each app's `views.py` |
| urls_example.py | `school_platform/urls.py` (main) |
| utils_and_commands.py | `scores/utils.py` + `*/management/commands/` |
| requirements.txt | Project root `requirements.txt` |
| .env.example | Project root `.env` (copy and configure) |
| SETUP_GUIDE.md | Project root or docs/ |
| PROJECT_SUMMARY.md | Project root or docs/ |
| README.md | Project root |
| setup.sh | Project root |

## 🔑 Key Implementation Points

### 1. Model Relationships
- All models are properly related with ForeignKey and OneToOne fields
- Cascade delete is set appropriately
- Indexes are included for performance

### 2. API Security
- JWT authentication on all endpoints except login/register
- Role-based permissions (Admin, Teacher, Student)
- Permission classes prevent unauthorized access

### 3. Calculation Logic
- Automatic percentage calculation in Score model
- Automatic grade assignment (A-F)
- Term result calculations aggregate scores
- Yearly results summarize terms

### 4. Bulk Operations
- Attendance bulk marking reduces API calls
- Batch result generation for entire class
- Efficient queries with select_related/prefetch_related

## ⚠️ Important Notes

### Database Setup
1. Must run `postgres_setup.sql` OR use Django migrations
2. If using migrations: `python manage.py migrate`
3. Never manually edit migration files

### Settings Configuration
1. Change SECRET_KEY in production
2. Set DEBUG = False for production
3. Configure CORS_ALLOWED_ORIGINS for frontend URL
4. Update EMAIL settings for notifications

### Deployment Preparation
1. Update settings.py for production
2. Collect static files: `python manage.py collectstatic`
3. Set up environment variables properly
4. Configure database backups
5. Use HTTPS in production

## 📊 Development Workflow

```
1. Create/edit model
   ↓
2. Create migration: python manage.py makemigrations
   ↓
3. Run migration: python manage.py migrate
   ↓
4. Create serializer for the model
   ↓
5. Create viewset in views.py
   ↓
6. Register in urls.py router
   ↓
7. Test API endpoint
   ↓
8. If admin needed, register in admin.py
```

## 🧪 Quick Testing Checklist

- [ ] All models created and migrated
- [ ] Admin site accessible
- [ ] Can create users in admin
- [ ] API /api/v1/ root page loads
- [ ] Login endpoint works
- [ ] JWT token received
- [ ] Can access protected endpoints with token
- [ ] Permissions work (admin can access, student can't)
- [ ] Attendance can be marked
- [ ] Scores can be recorded
- [ ] Results can be calculated
- [ ] Images can be uploaded

---

## 📝 Common File Paths

When implementing, you'll frequently need these locations:

```
Project Root/
├── manage.py                          # Django commands
├── school_platform/settings.py        # Main configuration
├── school_platform/urls.py            # API routing
├── users/models.py                    # User models
├── classes/models.py                  # Class models
├── attendance/models.py               # Attendance models
├── scores/models.py                   # Score/Result models
└── .env                              # Configuration
```

## 🎓 Learning Resources

As you implement, you may need to reference:
- Django ORM: https://docs.djangoproject.com/en/4.2/topics/db/models/
- DRF ViewSets: https://www.django-rest-framework.org/api-guide/viewsets/
- DRF Serializers: https://www.django-rest-framework.org/api-guide/serializers/
- JWT Auth: https://django-rest-framework-simplejwt.readthedocs.io/

---

**Ready to implement?** Start with Phase 1: Project Setup, then follow each phase sequentially!
