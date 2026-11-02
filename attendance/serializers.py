from rest_framework import serializers
from .models import Attendance, AttendanceSummary


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    term_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'class_obj', 'class_name', 'teacher',
                  'teacher_name', 'date', 'status', 'remarks', 'term', 'term_name']
        read_only_fields = ['id']

    def get_term_name(self, obj):
        return str(obj.term) if obj.term else '—'


class AttendanceSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    term_name = serializers.CharField(source='term.get_name_display', read_only=True)

    class Meta:
        model = AttendanceSummary
        fields = ['id', 'student', 'student_name', 'class_obj', 'class_name', 'term',
                  'term_name', 'total_school_days', 'total_present', 'total_absent',
                  'total_late', 'total_excused', 'attendance_percentage']
        read_only_fields = ['id']
