from rest_framework.routers import DefaultRouter
from .views import ClassViewSet, SubjectViewSet, TermViewSet

router = DefaultRouter()
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'terms', TermViewSet, basename='term')

urlpatterns = router.urls
