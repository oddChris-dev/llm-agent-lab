"""
WebSocket routing for executions.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/executions/(?P<execution_id>[^/]+)/$', consumers.ExecutionConsumer.as_asgi()),
]
