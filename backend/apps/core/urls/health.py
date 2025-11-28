"""
Health check URL patterns.
"""

from django.urls import path
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import time


def health_check(request):
    """
    Basic health check endpoint.
    Returns status of database and cache connections.
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }

    # Check database
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['checks']['database'] = {
            'status': 'healthy',
            'latency_ms': round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }

    # Check cache
    try:
        start = time.time()
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['checks']['cache'] = {
            'status': 'healthy',
            'latency_ms': round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        # Cache failure is not critical
        health_status['checks']['cache'] = {
            'status': 'degraded',
            'error': str(e)
        }

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


def liveness(request):
    """Simple liveness probe - just returns OK."""
    return JsonResponse({'status': 'ok'})


def readiness(request):
    """
    Readiness probe - checks if service is ready to accept traffic.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ready'})
    except Exception:
        return JsonResponse({'status': 'not_ready'}, status=503)


app_name = 'health'

urlpatterns = [
    path('', health_check, name='health'),
    path('live/', liveness, name='liveness'),
    path('ready/', readiness, name='readiness'),
]
