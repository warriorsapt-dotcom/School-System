from rest_framework import serializers
from .models import Score, ScoreComment, SubjectPerformance, TermResult, YearlyResult, ProgressLog


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
    term_name = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()

    class Meta:
        model = Score
        fields = ['id', 'student', 'student_name', 'class_subject', 'subject', 'subject_name',
                  'assessment_type', 'marks_obtained', 'max_marks', 'percentage',
                  'grade', 'term', 'term_name', 'remarks', 'is_approved']
        read_only_fields = ['id', 'percentage', 'grade']

    def get_grade(self, obj):
        return obj.get_grade()

    def get_term_name(self, obj):
        return str(obj.term) if obj.term else '—'


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
