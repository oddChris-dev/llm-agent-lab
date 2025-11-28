"""
URL patterns for executions.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExecutionViewSet

router = DefaultRouter()
router.register(r'', ExecutionViewSet, basename='execution')

app_name = 'executions'

urlpatterns = [
    path('', include(router.urls)),
]
