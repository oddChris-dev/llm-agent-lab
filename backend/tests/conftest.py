"""
Pytest configuration and fixtures for LLM Agent Lab tests.
"""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.workflows.models import Workflow, Node, Connection, WorkflowStatus
from apps.providers.models import Provider, ProviderType


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create and return a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def workflow(user):
    """Create and return a test workflow."""
    return Workflow.objects.create(
        name='Test Workflow',
        description='A test workflow',
        status=WorkflowStatus.DRAFT,
        user=user
    )


@pytest.fixture
def active_workflow(user):
    """Create and return an active workflow."""
    return Workflow.objects.create(
        name='Active Workflow',
        description='An active workflow',
        status=WorkflowStatus.ACTIVE,
        user=user
    )


@pytest.fixture
def node(workflow):
    """Create and return a test node."""
    return Node.objects.create(
        workflow=workflow,
        type='llm.claude',
        name='Test Node',
        position_x=100,
        position_y=100,
        config={'model': 'claude-3-opus'}
    )


@pytest.fixture
def provider(user):
    """Create and return a test provider."""
    return Provider.objects.create(
        name='Test Anthropic',
        slug='test-anthropic',
        type=ProviderType.LLM,
        config={'api_key': 'test-key'},
        user=user
    )


@pytest.fixture
def sample_workflow_data():
    """Return sample data for creating a workflow."""
    return {
        'name': 'New Workflow',
        'description': 'A new workflow for testing',
        'status': 'draft',
    }


@pytest.fixture
def sample_node_data():
    """Return sample data for creating a node."""
    return {
        'type': 'llm.claude',
        'name': 'Claude Node',
        'position': {'x': 200, 'y': 200},
        'config': {
            'model': 'claude-3-opus-20240229',
            'temperature': 0.7
        }
    }
