"""
URL patterns for providers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProviderViewSet

router = DefaultRouter()
router.register(r'', ProviderViewSet, basename='provider')

app_name = 'providers'

urlpatterns = [
    path('', include(router.urls)),
]
