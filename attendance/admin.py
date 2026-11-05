from django.contrib import admin
from .models import Attendance, AttendanceSummary

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'date', 'status', 'teacher')
    search_fields = ('student__admission_number', 'student__user__first_name', 'student__user__last_name')
    list_filter = ('status', 'date', 'class_obj')
    list_select_related = ('student__user', 'class_obj', 'teacher__user')


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'term', 'total_present', 'total_absent', 'attendance_percentage')
    search_fields = AttendanceAdmin.search_fields
    list_filter = ('term', 'class_obj')
    list_select_related = ('student__user', 'class_obj', 'term')
