from django.db import transaction
from django.db.models import Count, Q
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from attendance.models import Attendance
from scores.models import Score

from .models import Class, ClassSubject, Lesson, LibraryResource, Notice
from users.models import Teacher


class DashboardActivity(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        attendance = Attendance.objects.filter(date=today)
        scores = Score.objects.select_related('student__user', 'subject')
        if request.user.role == 'student':
            attendance = attendance.filter(student__user=request.user)
            scores = scores.filter(student__user=request.user)
        elif request.user.role == 'teacher':
            classes = Class.objects.filter(Q(class_teacher__user=request.user) |
                                           Q(class_subjects__teacher__user=request.user)).values('pk')
            attendance = attendance.filter(class_obj__in=classes)
            scores = scores.filter(Q(class_subject__teacher__user=request.user) |
                                   Q(class_subject__class_obj__class_teacher__user=request.user))
        elif request.user.role not in ('admin', 'principal'):
            return Response(status=403)
        counts = attendance.values('status').annotate(total=Count('pk')).order_by('status')
        recent = [{'student': row.student.user.get_full_name(), 'subject': row.subject.name,
                   'percentage': row.percentage} for row in scores.order_by('-date_recorded', '-pk')[:4]]
        return Response({'date': today, 'attendance': list(counts), 'scores': recent})


class SchoolContentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in permissions.SAFE_METHODS or request.user.role == 'admin'
        )


class LessonSerializer(serializers.ModelSerializer):
    academic_year = serializers.CharField(source='assignment.academic_year', read_only=True)
    class_name = serializers.CharField(source='assignment.class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='assignment.subject.name', read_only=True)
    day = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'assignment', 'academic_year', 'class_name', 'subject_name', 'weekday', 'day', 'starts', 'ends', 'room']

    def validate(self, attrs):
        def value(key):
            return attrs.get(key, getattr(self.instance, key, None))
        assignment = value('assignment')
        starts, ends = value('starts'), value('ends')
        if starts >= ends:
            raise serializers.ValidationError({'ends': 'Choose a time after the start.'})
        # Serialize schedule changes for the same class or subject teacher.
        Class.objects.select_for_update().get(pk=assignment.class_obj_id)
        conflict = Q(assignment__class_obj_id=assignment.class_obj_id)
        if assignment.teacher_id:
            Teacher.objects.select_for_update().get(pk=assignment.teacher_id)
            conflict |= Q(assignment__teacher_id=assignment.teacher_id)
        overlaps = Lesson.objects.filter(conflict, assignment__academic_year=assignment.academic_year,
                                        weekday=value('weekday'), starts__lt=ends, ends__gt=starts)
        if self.instance:
            overlaps = overlaps.exclude(pk=self.instance.pk)
        if overlaps.exists():
            raise serializers.ValidationError('This class or teacher already has a lesson at that time.', code='overlap')
        return attrs


class LessonViewSet(viewsets.ModelViewSet):
    permission_classes = [SchoolContentPermission]
    serializer_class = LessonSerializer
    filterset_fields = ['weekday', 'assignment__class_obj', 'assignment__academic_year']

    def get_queryset(self):
        qs = Lesson.objects.select_related('assignment__subject', 'assignment__class_obj')
        user = self.request.user
        if user.role == 'student':
            return qs.filter(assignment__class_obj__students__user=user)
        if user.role == 'teacher':
            return qs.filter(Q(assignment__teacher__user=user) | Q(assignment__class_obj__class_teacher__user=user))
        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @action(detail=False)
    def schedules(self, request):
        rows = self.get_queryset().values_list(
            'assignment__class_obj_id', 'assignment__class_obj__name', 'assignment__academic_year'
        ).order_by('-assignment__academic_year', 'assignment__class_obj__name').distinct()
        return Response([{'class_id': pk, 'name': name, 'year': year} for pk, name, year in rows])

    @action(detail=False)
    def distribution(self, request):
        return Response(self.get_queryset().values('weekday').annotate(total=Count('pk')).order_by('weekday'))

    @action(detail=False)
    def assignments(self, request):
        if request.user.role != 'admin':
            return Response(status=403)
        rows = ClassSubject.objects.select_related('class_obj', 'subject').order_by('class_obj__name', 'subject__name', 'academic_year')
        return Response([{'id': row.pk, 'label': f'{row.class_obj.name} · {row.subject.name} ({row.academic_year})'} for row in rows])


class LibrarySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = LibraryResource
        fields = ['id', 'title', 'subject', 'subject_name', 'url']

    def validate_url(self, value):
        if not value.lower().startswith(('https://', 'http://')):
            raise serializers.ValidationError('Enter an HTTP or HTTPS link.')
        return value


class LibraryViewSet(viewsets.ModelViewSet):
    permission_classes = [SchoolContentPermission]
    queryset = LibraryResource.objects.select_related('subject')
    serializer_class = LibrarySerializer
    search_fields = ['title', 'subject__name']


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['id', 'title', 'message', 'published']


class NoticeViewSet(viewsets.ModelViewSet):
    permission_classes = [SchoolContentPermission]
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    search_fields = ['title', 'message']
