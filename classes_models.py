"""
Classes app models - Class and Subject management
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Class(models.Model):
    """School class/form model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Form 1A, Form 2B")
    class_teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, related_name='classes_teaching')
    form_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    section = models.CharField(max_length=2, default='A')  # A, B, C, etc.
    stream = models.CharField(max_length=50, blank=True, null=True)  # Science, Arts, etc.
    capacity = models.IntegerField(default=50, validators=[MinValueValidator(1)])
    description = models.TextField(blank=True, null=True)
    year = models.IntegerField(default=2024, help_text="Academic year")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.year})"
    
    def get_student_count(self):
        """Get number of students in class"""
        return self.students.filter(is_active=True).count()
    
    class Meta:
        ordering = ['form_level', 'section']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        unique_together = ('name', 'year')


class Subject(models.Model):
    """Subject/Course model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_compulsory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'


class ClassSubject(models.Model):
    """Relationship between Class and Subject with assigned teacher"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='class_subjects')
    teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, related_name='teaching_assignments')
    academic_year = models.CharField(max_length=9, default='2024/2025')  # e.g., 2024/2025
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.class_obj.name} - {self.subject.name} ({self.teacher})"
    
    class Meta:
        unique_together = ('class_obj', 'subject', 'academic_year')
        verbose_name = 'Class Subject'
        verbose_name_plural = 'Class Subjects'


class Term(models.Model):
    """Academic term model"""
    
    TERM_CHOICES = (
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=TERM_CHOICES)
    academic_year = models.CharField(max_length=9, default='2024/2025')  # e.g., 2024/2025
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_name_display()} {self.academic_year}"
    
    def is_ongoing(self):
        """Check if term is currently ongoing"""
        from datetime import date
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    class Meta:
        ordering = ['academic_year', 'name']
        unique_together = ('name', 'academic_year')
        verbose_name = 'Academic Term'
        verbose_name_plural = 'Academic Terms'
