from rest_framework import serializers
from .models import Class, Subject, ClassSubject, Term
from users.serializers import StudentSerializer


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
