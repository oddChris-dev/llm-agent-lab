"""
URL patterns for assets.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet

router = DefaultRouter()
router.register(r'', AssetViewSet, basename='asset')

app_name = 'assets'

urlpatterns = [
    path('', include(router.urls)),
]
