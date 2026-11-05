from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

from .models import CustomUser, Teacher, Student, SchoolImage
from .serializers import (
    CustomUserSerializer, TeacherSerializer, StudentSerializer,
    SchoolImageSerializer, LoginSerializer, RegistrationSerializer, ChangePasswordSerializer,
)
from classes.serializers import ClassSerializer, ClassSubjectSerializer
from scores.serializers import TermResultSerializer, ProgressLogSerializer


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'teacher'


class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ('teacher', 'admin')


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.role == 'admin'
        return request.user == obj or request.user.role == 'admin'


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, username=email, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': CustomUserSerializer(user).data
                }, status=status.HTTP_200_OK)
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if request.user.check_password(serializer.validated_data['old_password']):
                request.user.set_password(serializer.validated_data['new_password'])
                request.user.save()
                return Response({'detail': 'Password changed successfully'}, status=status.HTTP_200_OK)
            return Response({'detail': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(CustomUserSerializer(request.user).data)

    def put(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.select_related('user').all()
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_class_teacher', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']
    ordering_fields = ['user__first_name', 'hire_date']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            teacher = request.user.teacher_profile
        except Exception:
            return Response({'error': 'Not a teacher'}, status=status.HTTP_404_NOT_FOUND)
        data = TeacherSerializer(teacher).data
        my_class = teacher.classes_teaching.select_related('class_teacher__user').first()
        data['my_class'] = ClassSerializer(my_class).data if my_class else None
        return Response(data)

    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        teacher = self.get_object()
        serializer = ClassSerializer(teacher.classes_teaching.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        teacher = self.get_object()
        serializer = ClassSubjectSerializer(teacher.teaching_assignments.all(), many=True)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['class_assigned', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'admission_number']
    ordering_fields = ['user__first_name', 'admission_date']

    def get_queryset(self):
        qs = Student.objects.select_related('user', 'class_assigned')
        if self.request.user.role == 'student':
            return qs.filter(user=self.request.user)
        if self.request.user.role == 'teacher':
            try:
                teacher = self.request.user.teacher_profile
                class_ids = teacher.teaching_assignments.values_list('class_obj_id', flat=True)
                qs = qs.filter(Q(class_assigned__in=class_ids) | Q(class_assigned__class_teacher=teacher))
            except Exception:
                return qs.none()
        return qs.all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        if self.action == 'attendance_history':
            return [permissions.IsAuthenticated(), IsTeacherOrAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def attendance_history(self, request, pk=None):
        from attendance.models import Attendance
        from attendance.serializers import AttendanceSerializer

        student = self.get_object()

        class HistoryFilters(serializers.Serializer):
            start_date = serializers.DateField(required=False)
            end_date = serializers.DateField(required=False)
            status = serializers.ChoiceField(choices=Attendance.STATUS_CHOICES, required=False)

            def validate(self, data):
                if data.get('start_date') and data.get('end_date') and data['start_date'] > data['end_date']:
                    raise serializers.ValidationError('Start date must be on or before end date.')
                return data

        filters = HistoryFilters(data=request.query_params)
        filters.is_valid(raise_exception=True)
        qs = student.attendance_records.select_related('student__user', 'class_obj', 'teacher__user', 'term').order_by('-date', '-pk')
        for key, lookup in [('start_date', 'date__gte'), ('end_date', 'date__lte'), ('status', 'status')]:
            if key in filters.validated_data:
                qs = qs.filter(**{lookup: filters.validated_data[key]})
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(AttendanceSerializer(page, many=True).data)
        return Response(AttendanceSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        student = self.get_object()
        qs = student.term_results.all()
        term_id = request.query_params.get('term')
        if term_id:
            qs = qs.filter(term_id=term_id)
        return Response(TermResultSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        student = self.get_object()
        qs = student.progress_logs.all().order_by('recorded_date')
        return Response(ProgressLogSerializer(qs, many=True).data)


class SchoolImageViewSet(viewsets.ModelViewSet):
    queryset = SchoolImage.objects.filter(is_published=True)
    serializer_class = SchoolImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_published']
    search_fields = ['title', 'description']
    ordering_fields = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class SchoolConfigurationView(APIView):
    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdmin()]

    def get(self, request):
        from .models import SchoolConfiguration
        from .serializers import SchoolConfigurationSerializer
        return Response(SchoolConfigurationSerializer(SchoolConfiguration.current()).data)

    def patch(self, request):
        from .models import SchoolConfiguration
        from .serializers import SchoolConfigurationSerializer
        serializer = SchoolConfigurationSerializer(SchoolConfiguration.current(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
