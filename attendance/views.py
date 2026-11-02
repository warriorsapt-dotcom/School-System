from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Attendance, AttendanceSummary
from .serializers import AttendanceSerializer, AttendanceSummarySerializer
from users.views import IsAdmin, IsTeacher, IsTeacherOrAdmin


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'class_obj', 'date', 'status', 'term']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    ordering_fields = ['date']

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            'student__user', 'class_obj', 'teacher__user', 'term'
        )
        if self.request.user.role == 'student':
            qs = qs.filter(student__user=self.request.user)
        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_mark']:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            teacher = self.request.user.teacher_profile
        except Exception:
            teacher = None
        serializer.save(teacher=teacher)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        qs = AttendanceSummary.objects.all()
        if request.user.role == 'student':
            qs = qs.filter(student__user=request.user)
        student_id = request.query_params.get('student')
        class_id = request.query_params.get('class')
        term_id = request.query_params.get('term')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if class_id:
            qs = qs.filter(class_obj_id=class_id)
        if term_id:
            qs = qs.filter(term_id=term_id)
        return Response(AttendanceSummarySerializer(qs, many=True).data)

    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        created = []
        for attendance_data in request.data.get('attendances', []):
            serializer = self.get_serializer(data=attendance_data)
            if serializer.is_valid():
                self.perform_create(serializer)
                created.append(serializer.data)
        return Response({'created': created}, status=status.HTTP_201_CREATED)
