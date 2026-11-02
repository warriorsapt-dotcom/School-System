"""
Django REST Framework Views and ViewSets for School Platform
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import datetime, timedelta

from users.models import CustomUser, Teacher, Student, Admin, SchoolImage
from classes.models import Class, Subject, ClassSubject, Term
from attendance.models import Attendance, AttendanceSummary
from scores.models import Score, ScoreComment, SubjectPerformance, TermResult, YearlyResult, ProgressLog

# Import serializers
from serializers_example import (
    CustomUserSerializer, TeacherSerializer, StudentSerializer, AdminSerializer,
    SchoolImageSerializer, SubjectSerializer, ClassSerializer, ClassDetailSerializer,
    ClassSubjectSerializer, TermSerializer, AttendanceSerializer, AttendanceSummarySerializer,
    ScoreSerializer, ScoreDetailSerializer, ScoreCommentSerializer, SubjectPerformanceSerializer,
    TermResultSerializer, YearlyResultSerializer, ProgressLogSerializer,
    LoginSerializer, RegistrationSerializer, ChangePasswordSerializer
)


# ============== Permissions ==============

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'teacher'


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'student'


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.role == 'admin'
        return request.user == obj or request.user.role == 'admin'


# ============== Authentication Views ==============

class LoginView(APIView):
    """
    POST: Login user and get tokens
    """
    permission_classes = [permissions.AllowAny]
    
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
    """
    POST: Register new user
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
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
    """
    POST: Logout user (blacklist refresh token)
    """
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
    """
    POST: Change user password
    """
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
    """
    GET: Get current user profile
    PUT: Update current user profile
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============== Users ViewSets ==============

class TeacherViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for teachers
    """
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_class_teacher', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']
    ordering_fields = ['user__first_name', 'hire_date']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """Get classes assigned to this teacher"""
        teacher = self.get_object()
        classes = teacher.classes_teaching.all()
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """Get subjects taught by this teacher"""
        teacher = self.get_object()
        class_subjects = teacher.teaching_assignments.all()
        serializer = ClassSubjectSerializer(class_subjects, many=True)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for students
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['class_assigned', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'admission_number']
    ordering_fields = ['user__first_name', 'admission_date']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get student term results"""
        student = self.get_object()
        term_id = request.query_params.get('term')
        
        results = student.term_results.all()
        if term_id:
            results = results.filter(term_id=term_id)
        
        serializer = TermResultSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get student progress over all terms"""
        student = self.get_object()
        progress = student.progress_logs.all().order_by('recorded_date')
        serializer = ProgressLogSerializer(progress, many=True)
        return Response(serializer.data)


# ============== Classes & Subjects ViewSets ==============

class ClassViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for classes
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['form_level', 'is_active']
    search_fields = ['name', 'stream']
    ordering_fields = ['form_level', 'section']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClassDetailSerializer
        return ClassSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Get attendance for a class"""
        class_obj = self.get_object()
        attendance = Attendance.objects.filter(class_obj=class_obj)
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)


class SubjectViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for subjects
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'code']
    ordering_fields = ['name']


class TermViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only operations for academic terms
    """
    queryset = Term.objects.all()
    serializer_class = TermSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['academic_year', 'is_current']
    ordering_fields = ['-academic_year', 'name']


# ============== Attendance ViewSets ==============

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    Attendance marking and tracking
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'class_obj', 'date', 'status', 'term']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    ordering_fields = ['-date']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacher() | IsAdmin()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher_profile)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get attendance summary"""
        student_id = request.query_params.get('student')
        class_id = request.query_params.get('class')
        term_id = request.query_params.get('term')
        
        summaries = AttendanceSummary.objects.all()
        if student_id:
            summaries = summaries.filter(student_id=student_id)
        if class_id:
            summaries = summaries.filter(class_obj_id=class_id)
        if term_id:
            summaries = summaries.filter(term_id=term_id)
        
        serializer = AttendanceSummarySerializer(summaries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Bulk mark attendance for a class"""
        attendances = request.data.get('attendances', [])
        created = []
        
        for attendance_data in attendances:
            serializer = self.get_serializer(data=attendance_data)
            if serializer.is_valid():
                self.perform_create(serializer)
                created.append(serializer.data)
        
        return Response({'created': created}, status=status.HTTP_201_CREATED)


# ============== Scores & Results ViewSets ==============

class ScoreViewSet(viewsets.ModelViewSet):
    """
    Record and view student scores
    """
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'subject', 'term', 'assessment_type']
    search_fields = ['student__user__first_name', 'subject__name']
    ordering_fields = ['-date_recorded', 'percentage']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacher() | IsAdmin()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ScoreDetailSerializer
        return ScoreSerializer
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to a score"""
        score = self.get_object()
        serializer = ScoreCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(score=score, teacher=request.user.teacher_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def student_scores(self, request):
        """Get all scores for a student"""
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        scores = Score.objects.filter(student_id=student_id)
        serializer = ScoreSerializer(scores, many=True)
        return Response(serializer.data)


class TermResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View term results
    """
    queryset = TermResult.objects.all()
    serializer_class = TermResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['student', 'term', 'class_obj', 'status']
    ordering_fields = ['position_in_class', '-average_percentage']
    
    @action(detail=False, methods=['get'])
    def class_ranking(self, request):
        """Get class ranking for a term"""
        class_id = request.query_params.get('class')
        term_id = request.query_params.get('term')
        
        if not (class_id and term_id):
            return Response({'error': 'class and term parameters required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        results = TermResult.objects.filter(
            class_obj_id=class_id,
            term_id=term_id
        ).order_by('position_in_class')
        
        serializer = TermResultSerializer(results, many=True)
        return Response(serializer.data)


class ProgressChartView(APIView):
    """
    Get data for progress charts
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get progress data
        progress_data = student.progress_logs.all().order_by('recorded_date')
        
        # Format for charts
        chart_data = {
            'labels': [log.get_name_display() for log in progress_data],
            'datasets': [{
                'label': 'Average Percentage',
                'data': [float(log.average_percentage) for log in progress_data],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            }]
        }
        
        return Response(chart_data)


# ============== Image Management ViewSet ==============

class SchoolImageViewSet(viewsets.ModelViewSet):
    """
    Upload and manage school images
    """
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
