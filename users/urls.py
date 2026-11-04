from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    SchoolConfigurationView, LoginView, RegisterView, LogoutView, ChangePasswordView, ProfileView,
    TeacherViewSet, StudentViewSet, SchoolImageViewSet,
)

router = DefaultRouter()
router.register(r'users/teachers', TeacherViewSet, basename='teacher')
router.register(r'users/students', StudentViewSet, basename='student')
router.register(r'images', SchoolImageViewSet, basename='image')

urlpatterns = [
    path('school-settings/', SchoolConfigurationView.as_view(), name='school-settings'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
] + router.urls
