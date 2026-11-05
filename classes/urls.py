from rest_framework.routers import DefaultRouter
from .views import ClassViewSet, SubjectViewSet, TermViewSet
from django.urls import path
from .workspace import DashboardActivity, LessonViewSet, LibraryViewSet, NoticeViewSet

router = DefaultRouter()
router.register('timetable', LessonViewSet, basename='lesson')
router.register('library', LibraryViewSet)
router.register('notices', NoticeViewSet)
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'terms', TermViewSet, basename='term')

urlpatterns = [path('dashboard-activity/', DashboardActivity.as_view())] + router.urls
