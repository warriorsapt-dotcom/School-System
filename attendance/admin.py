from django.contrib import admin
from .models import Attendance, AttendanceSummary

admin.site.register(Attendance)
admin.site.register(AttendanceSummary)
