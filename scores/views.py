import csv
from django.http import HttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Score, ScoreComment, TermResult
from users.models import Student
from .serializers import (
    ScoreSerializer, ScoreDetailSerializer, ScoreCommentSerializer,
    TermResultSerializer, ProgressLogSerializer,
)
from users.views import IsAdmin, IsTeacher, IsTeacherOrAdmin


class ScoreViewSet(viewsets.ModelViewSet):
    serializer_class = ScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'subject', 'term', 'assessment_type']
    search_fields = ['student__user__first_name', 'subject__name']
    ordering_fields = ['-date_recorded', 'percentage']

    def get_queryset(self):
        qs = Score.objects.select_related(
            'student__user', 'subject', 'class_subject__class_obj', 'term'
        )
        if self.request.user.role == 'student':
            qs = qs.filter(student__user=self.request.user)
        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ScoreDetailSerializer
        return ScoreSerializer

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        score = self.get_object()
        serializer = ScoreCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(score=score, teacher=request.user.teacher_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def student_scores(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        scores = Score.objects.filter(student_id=student_id)
        return Response(ScoreSerializer(scores, many=True).data)


class TermResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TermResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'term', 'class_obj', 'status']

    def get_queryset(self):
        qs = TermResult.objects.select_related(
            'student__user', 'term', 'class_obj', 'best_subject', 'worst_subject'
        )
        if self.request.user.role == 'student':
            qs = qs.filter(student__user=self.request.user)
        return qs

    @action(detail=False, methods=['get'])
    def class_ranking(self, request):
        class_id = request.query_params.get('class')
        term_id = request.query_params.get('term')
        if not (class_id and term_id):
            return Response({'error': 'class and term parameters required'}, status=status.HTTP_400_BAD_REQUEST)
        results = TermResult.objects.filter(
            class_obj_id=class_id, term_id=term_id
        ).order_by('position_in_class')
        return Response(TermResultSerializer(results, many=True).data)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="term_results.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student', 'Class', 'Term', 'Average %', 'Grade', 'Position',
                         'Subjects Passed', 'Subjects Failed', 'Status'])
        for r in qs:
            writer.writerow([
                r.student.user.get_full_name(),
                r.class_obj.name,
                str(r.term),
                r.average_percentage,
                r.overall_grade,
                r.position_in_class,
                r.subjects_passed,
                r.subjects_failed,
                r.status,
            ])
        return response


class ProgressChartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        progress_data = student.progress_logs.all().order_by('recorded_date')
        chart_data = {
            'labels': [
                log.term.get_name_display() if log.term else log.academic_year
                for log in progress_data
            ],
            'datasets': [{
                'label': 'Average Percentage',
                'data': [float(log.average_percentage) for log in progress_data],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            }]
        }
        return Response(chart_data)
