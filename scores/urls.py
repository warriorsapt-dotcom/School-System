from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ScoreViewSet, TermResultViewSet, ProgressChartView

router = DefaultRouter()
router.register(r'scores', ScoreViewSet, basename='score')
router.register(r'results', TermResultViewSet, basename='result')

urlpatterns = [
    path('progress/chart/', ProgressChartView.as_view(), name='progress-chart'),
] + router.urls
