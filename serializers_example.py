"""
Django REST Framework Serializers for School Platform
"""

from rest_framework import serializers
from users.models import CustomUser, Teacher, Student, Admin, SchoolImage
from classes.models import Class, Subject, ClassSubject, Term
from attendance.models import Attendance, AttendanceSummary
from scores.models import Score, ScoreComment, SubjectPerformance, TermResult, YearlyResult, ProgressLog


# ============== Users Serializers ==============

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone_number', 
                  'role', 'password', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class TeacherSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'employee_id', 'qualification', 'subject_specialization', 
                  'bio', 'hire_date', 'is_class_teacher', 'is_active']
        read_only_fields = ['id']


class StudentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    class_assigned_name = serializers.CharField(source='class_assigned.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'user', 'admission_number', 'class_assigned', 'class_assigned_name',
                  'date_of_birth', 'parent_name', 'parent_contact', 'parent_email', 
                  'address', 'is_active']
        read_only_fields = ['id']


class AdminSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Admin
        fields = ['id', 'user', 'employee_id', 'department', 'designation']
        read_only_fields = ['id']


class SchoolImageSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = SchoolImage
        fields = ['id', 'title', 'description', 'image', 'category', 'uploaded_by', 
                  'uploaded_by_name', 'is_published', 'created_at']
        read_only_fields = ['id', 'created_at', 'uploaded_by']


# ============== Classes & Subjects Serializers ==============

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'description', 'is_compulsory', 'is_active']
        read_only_fields = ['id']


class ClassSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    
    class Meta:
        model = ClassSubject
        fields = ['id', 'class_obj', 'class_name', 'subject', 'subject_name', 'teacher', 
                  'teacher_name', 'academic_year']
        read_only_fields = ['id']


class ClassSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.CharField(source='class_teacher.user.get_full_name', read_only=True)
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = ['id', 'name', 'class_teacher', 'class_teacher_name', 'form_level', 
                  'section', 'stream', 'capacity', 'student_count', 'description', 
                  'year', 'is_active']
        read_only_fields = ['id', 'student_count']
    
    def get_student_count(self, obj):
        return obj.get_student_count()


class ClassDetailSerializer(ClassSerializer):
    students = StudentSerializer(many=True, read_only=True, source='students.all')
    class_subjects = ClassSubjectSerializer(many=True, read_only=True)


class TermSerializer(serializers.ModelSerializer):
    is_ongoing = serializers.SerializerMethodField()
    
    class Meta:
        model = Term
        fields = ['id', 'name', 'academic_year', 'start_date', 'end_date', 'is_current', 
                  'is_active', 'is_ongoing']
        read_only_fields = ['id']
    
    def get_is_ongoing(self, obj):
        return obj.is_ongoing()


# ============== Attendance Serializers ==============

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'class_obj', 'class_name', 'teacher', 
                  'teacher_name', 'date', 'status', 'remarks', 'term']
        read_only_fields = ['id']


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


# ============== Scores & Results Serializers ==============

class ScoreCommentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = ScoreComment
        fields = ['id', 'score', 'teacher', 'teacher_name', 'comment_text', 'comment_type', 
                  'is_visible_to_student', 'created_at']
        read_only_fields = ['id', 'created_at', 'teacher']


class ScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade = serializers.SerializerMethodField()
    
    class Meta:
        model = Score
        fields = ['id', 'student', 'student_name', 'subject', 'subject_name', 
                  'assessment_type', 'marks_obtained', 'max_marks', 'percentage', 
                  'grade', 'term', 'remarks', 'is_approved']
        read_only_fields = ['id', 'percentage', 'grade']
    
    def get_grade(self, obj):
        return obj.get_grade()


class ScoreDetailSerializer(ScoreSerializer):
    comments = ScoreCommentSerializer(many=True, read_only=True)


class SubjectPerformanceSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    
    class Meta:
        model = SubjectPerformance
        fields = ['id', 'student', 'student_name', 'subject', 'subject_name', 'term',
                  'total_marks', 'max_marks', 'average_percentage', 'number_of_assessments',
                  'grade', 'rank_in_class', 'comments']
        read_only_fields = ['id']


class TermResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    best_subject_name = serializers.CharField(source='best_subject.name', read_only=True)
    worst_subject_name = serializers.CharField(source='worst_subject.name', read_only=True)
    
    class Meta:
        model = TermResult
        fields = ['id', 'student', 'student_name', 'term', 'class_obj', 'class_name',
                  'total_marks', 'total_max_marks', 'average_percentage', 'position_in_class',
                  'total_students_in_class', 'overall_grade', 'subjects_passed', 
                  'subjects_failed', 'best_subject', 'best_subject_name', 'worst_subject',
                  'worst_subject_name', 'status', 'principal_comment', 'class_teacher_comment']
        read_only_fields = ['id']


class YearlyResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    term1_average = serializers.SerializerMethodField()
    term2_average = serializers.SerializerMethodField()
    term3_average = serializers.SerializerMethodField()
    
    class Meta:
        model = YearlyResult
        fields = ['id', 'student', 'student_name', 'academic_year', 'annual_average',
                  'term1_average', 'term2_average', 'term3_average', 'improvement_trend',
                  'principal_remarks']
        read_only_fields = ['id']
    
    def get_term1_average(self, obj):
        return obj.term1_result.average_percentage if obj.term1_result else None
    
    def get_term2_average(self, obj):
        return obj.term2_result.average_percentage if obj.term2_result else None
    
    def get_term3_average(self, obj):
        return obj.term3_result.average_percentage if obj.term3_result else None


class ProgressLogSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    term_name = serializers.CharField(source='term.get_name_display', read_only=True)
    
    class Meta:
        model = ProgressLog
        fields = ['id', 'student', 'student_name', 'term', 'term_name', 'academic_year',
                  'average_percentage', 'rank_in_class', 'subjects_passed', 'subjects_failed',
                  'improvement_flag', 'notes', 'recorded_date']
        read_only_fields = ['id', 'recorded_date']


# ============== Authentication Serializers ==============

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
    
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords must match'})
        return data
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords must match'})
        return data
