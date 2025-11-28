"""
Django development settings for LLM Agent Lab.

These settings are optimized for local development with hot reloading.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - SQLite for easy local development, PostgreSQL for production-like testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'agent_lab'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Alternative: SQLite for quick local testing
if os.environ.get('USE_SQLITE', 'false').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# CORS - Allow all in development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# For hot reloading with webpack dev server
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

# Disable WhiteNoise compression in development for faster reloads
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Django Debug Toolbar (optional but recommended)
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Use simpler channel layer for development (no Redis required)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Email - Console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging - More verbose in development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING',  # Set to DEBUG to see SQL queries
    'propagate': False,
}

# REST Framework - Allow browsable API in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += [
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Celery - Use same process for easy debugging (no Redis required)
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_EAGER', 'true').lower() == 'true'
CELERY_TASK_EAGER_PROPAGATES = True

# Cache - Local memory cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Print SQL queries count at end of each request (useful for N+1 detection)
# Uncomment to enable:
# MIDDLEWARE += ['apps.core.middleware.QueryCountMiddleware']
