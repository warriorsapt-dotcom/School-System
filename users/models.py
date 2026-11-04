from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from .validators import validate_account_id, validate_account_suffix


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('principal', 'Principal / Head Teacher'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField('email or school login ID', max_length=254, unique=True, validators=[validate_account_id])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    qualification = models.CharField(max_length=255, blank=True, help_text="e.g., B.Ed, M.Sc")
    subject_specialization = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    is_class_teacher = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.subject_specialization}"

    class Meta:
        ordering = ['user__first_name']
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=50, unique=True)
    class_assigned = models.ForeignKey('classes.Class', on_delete=models.SET_NULL, null=True, related_name='students')
    date_of_birth = models.DateField(blank=True, null=True)
    parent_name = models.CharField(max_length=255, blank=True)
    parent_contact = models.CharField(max_length=15, blank=True)
    parent_email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    admission_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.admission_number}"

    def get_age(self):
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    class Meta:
        ordering = ['user__first_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'


class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin - {self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'


class SchoolImage(models.Model):
    CATEGORY_CHOICES = (
        ('school', 'School Facilities'),
        ('events', 'Events'),
        ('activities', 'Activities'),
        ('achievements', 'Achievements'),
        ('news', 'News'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='school_images/%Y/%m/%d/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='school')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='uploaded_images')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'School Image'
        verbose_name_plural = 'School Images'


class SchoolConfiguration(models.Model):
    """One school per installation; this does not introduce multi-school tenancy."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    school_name = models.CharField(max_length=150, default='School System')
    account_suffix = models.CharField(max_length=100, default='school.com', validators=[validate_account_suffix], help_text='For example ksc or ktp. Used for new login IDs; this does not create email inboxes.')

    class Meta:
        verbose_name = 'School settings'
        verbose_name_plural = 'School settings'
        constraints = [models.CheckConstraint(check=models.Q(id=1), name='single_school_configuration')]

    def save(self, *args, **kwargs):
        self.pk = 1
        self.school_name = self.school_name.strip()
        self.account_suffix = self.account_suffix.strip().lower()
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        return cls.objects.filter(pk=1).first() or cls()

    def __str__(self):
        return self.school_name
