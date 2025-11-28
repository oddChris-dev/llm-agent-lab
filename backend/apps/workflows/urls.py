"""
URL patterns for workflow management.
"""

from django.urls import path, include
from rest_framework_nested import routers
from .views import WorkflowViewSet, NodeViewSet, ConnectionViewSet

# Main router for workflows
router = routers.DefaultRouter()
router.register(r'', WorkflowViewSet, basename='workflow')

# Nested router for nodes within workflows
workflows_router = routers.NestedDefaultRouter(router, r'', lookup='workflow')
workflows_router.register(r'nodes', NodeViewSet, basename='workflow-nodes')
workflows_router.register(r'connections', ConnectionViewSet, basename='workflow-connections')

app_name = 'workflows'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(workflows_router.urls)),
]
