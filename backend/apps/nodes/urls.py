"""
URL patterns for node types.
"""

from django.urls import path
from .views import NodeTypeListView, NodeTypeDetailView

app_name = 'nodes'

urlpatterns = [
    path('', NodeTypeListView.as_view(), name='list'),
    path('<path:type_id>/', NodeTypeDetailView.as_view(), name='detail'),
]
