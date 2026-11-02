"""
URL Configuration for School Platform API
Place this in school_platform/urls.py
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import views
from views_example import (
    LoginView, RegisterView, LogoutView, ChangePasswordView, ProfileView,
    TeacherViewSet, StudentViewSet, ClassViewSet, SubjectViewSet, TermViewSet,
    AttendanceViewSet, ScoreViewSet, TermResultViewSet, ProgressChartView,
    SchoolImageViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users/teachers', TeacherViewSet, basename='teacher')
router.register(r'users/students', StudentViewSet, basename='student')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'terms', TermViewSet, basename='term')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'scores', ScoreViewSet, basename='score')
router.register(r'results', TermResultViewSet, basename='result')
router.register(r'images', SchoolImageViewSet, basename='image')

# API URL patterns
api_patterns = [
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Progress and analytics
    path('progress/chart/', ProgressChartView.as_view(), name='progress-chart'),
    
    # Include router URLs
    path('', include(router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include(api_patterns)),
    
    # API authentication (optional - for browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = 'School Management Platform'
admin.site.site_title = 'School Admin'
