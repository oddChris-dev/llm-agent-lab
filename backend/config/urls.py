"""
URL configuration for LLM Agent Lab.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# API v1 URL patterns
api_v1_patterns = [
    path('workflows/', include('apps.workflows.urls')),
    path('providers/', include('apps.providers.urls')),
    path('queues/', include('apps.queues.urls')),
    path('executions/', include('apps.executions.urls')),
    path('assets/', include('apps.assets.urls')),
    path('node-types/', include('apps.nodes.urls')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include(api_v1_patterns)),

    # Authentication
    path('api/v1/auth/', include('apps.core.urls.auth')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health check
    path('health/', include('apps.core.urls.health')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
