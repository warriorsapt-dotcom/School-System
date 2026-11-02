"""
Attendance app models - Student attendance tracking
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Attendance(models.Model):
    """Student attendance record"""
    
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absent'),
        ('medical', 'Medical Leave'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='attendance_records')
    class_obj = models.ForeignKey('classes.Class', on_delete=models.CASCADE, related_name='attendance_records')
    teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, related_name='attendance_marked')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    remarks = models.TextField(blank=True, null=True)
    term = models.ForeignKey('classes.Term', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student} - {self.date} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'date', 'class_obj')
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['student']),
            models.Index(fields=['class_obj']),
        ]


class AttendanceSummary(models.Model):
    """Monthly/Term attendance summary for quick reporting"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='attendance_summaries')
    class_obj = models.ForeignKey('classes.Class', on_delete=models.CASCADE)
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE)
    total_school_days = models.IntegerField(default=0)
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    total_excused = models.IntegerField(default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    calculated_date = models.DateTimeField(auto_now=True)
    
    def calculate_attendance_percentage(self):
        """Calculate attendance percentage"""
        if self.total_school_days > 0:
            self.attendance_percentage = (self.total_present / self.total_school_days) * 100
        return self.attendance_percentage
    
    def __str__(self):
        return f"{self.student} - {self.term} ({self.attendance_percentage}%)"
    
    class Meta:
        unique_together = ('student', 'class_obj', 'term')
        verbose_name = 'Attendance Summary'
        verbose_name_plural = 'Attendance Summaries'
