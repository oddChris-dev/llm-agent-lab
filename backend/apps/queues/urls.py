"""
URL patterns for queues.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QueueViewSet

router = DefaultRouter()
router.register(r'', QueueViewSet, basename='queue')

app_name = 'queues'

urlpatterns = [
    path('', include(router.urls)),
]
