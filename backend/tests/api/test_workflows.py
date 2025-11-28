"""
API tests for workflow endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.workflows.models import Workflow, WorkflowStatus


@pytest.mark.django_db
class TestWorkflowAPI:
    """Test workflow CRUD operations."""

    def test_list_workflows_unauthenticated(self, api_client):
        """Unauthenticated requests should return 401."""
        url = reverse('workflows:workflow-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_workflows_empty(self, authenticated_client):
        """List workflows returns empty list when none exist."""
        url = reverse('workflows:workflow-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data'] == []

    def test_list_workflows(self, authenticated_client, workflow):
        """List workflows returns user's workflows."""
        url = reverse('workflows:workflow-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == workflow.name

    def test_create_workflow(self, authenticated_client, sample_workflow_data):
        """Create a new workflow."""
        url = reverse('workflows:workflow-list')
        response = authenticated_client.post(url, sample_workflow_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == sample_workflow_data['name']
        assert Workflow.objects.count() == 1

    def test_get_workflow(self, authenticated_client, workflow):
        """Get workflow detail."""
        url = reverse('workflows:workflow-detail', kwargs={'pk': workflow.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == workflow.name
        assert 'nodes' in response.data['data']
        assert 'connections' in response.data['data']

    def test_update_workflow(self, authenticated_client, workflow):
        """Update workflow."""
        url = reverse('workflows:workflow-detail', kwargs={'pk': workflow.id})
        response = authenticated_client.patch(
            url,
            {'name': 'Updated Name'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        workflow.refresh_from_db()
        assert workflow.name == 'Updated Name'

    def test_delete_workflow(self, authenticated_client, workflow):
        """Delete (soft-delete) workflow."""
        url = reverse('workflows:workflow-detail', kwargs={'pk': workflow.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        workflow.refresh_from_db()
        assert workflow.deleted_at is not None

    def test_duplicate_workflow(self, authenticated_client, workflow, node):
        """Duplicate workflow with nodes."""
        url = reverse('workflows:workflow-duplicate', kwargs={'pk': workflow.id})
        response = authenticated_client.post(
            url,
            {'name': 'Duplicated Workflow'},
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == 'Duplicated Workflow'
        assert Workflow.objects.count() == 2

    def test_filter_workflows_by_status(self, authenticated_client, workflow, active_workflow):
        """Filter workflows by status."""
        url = reverse('workflows:workflow-list')
        response = authenticated_client.get(url, {'status': 'active'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['status'] == 'active'

    def test_search_workflows(self, authenticated_client, workflow):
        """Search workflows by name."""
        url = reverse('workflows:workflow-list')
        response = authenticated_client.get(url, {'search': 'Test'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1

    def test_user_isolation(self, authenticated_client, user):
        """Users can only see their own workflows."""
        # Create another user's workflow
        from django.contrib.auth.models import User
        other_user = User.objects.create_user('other', 'other@test.com', 'pass')
        Workflow.objects.create(
            name='Other Workflow',
            user=other_user,
            status=WorkflowStatus.DRAFT
        )

        url = reverse('workflows:workflow-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Should not see other user's workflow
        assert len(response.data['data']) == 0


@pytest.mark.django_db
class TestNodeAPI:
    """Test node operations within workflows."""

    def test_create_node(self, authenticated_client, workflow, sample_node_data):
        """Create a node in a workflow."""
        url = reverse('workflows:workflow-nodes-list', kwargs={'workflow_pk': workflow.id})
        response = authenticated_client.post(url, sample_node_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['type'] == sample_node_data['type']

    def test_update_node_position(self, authenticated_client, workflow, node):
        """Update node position."""
        url = reverse(
            'workflows:workflow-nodes-detail',
            kwargs={'workflow_pk': workflow.id, 'pk': node.id}
        )
        response = authenticated_client.patch(
            url,
            {'position': {'x': 500, 'y': 300}},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        node.refresh_from_db()
        assert node.position_x == 500
        assert node.position_y == 300

    def test_batch_update_nodes(self, authenticated_client, workflow):
        """Batch update multiple nodes."""
        from apps.workflows.models import Node
        node1 = Node.objects.create(
            workflow=workflow, type='llm.claude',
            position_x=0, position_y=0
        )
        node2 = Node.objects.create(
            workflow=workflow, type='voice.tts',
            position_x=0, position_y=0
        )

        url = reverse('workflows:workflow-nodes-batch', kwargs={'workflow_pk': workflow.id})
        response = authenticated_client.patch(
            url,
            {
                'updates': [
                    {'id': str(node1.id), 'position': {'x': 100, 'y': 100}},
                    {'id': str(node2.id), 'position': {'x': 200, 'y': 200}},
                ]
            },
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated'] == 2

    def test_delete_node(self, authenticated_client, workflow, node):
        """Delete a node."""
        url = reverse(
            'workflows:workflow-nodes-detail',
            kwargs={'workflow_pk': workflow.id, 'pk': node.id}
        )
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestConnectionAPI:
    """Test connection operations."""

    def test_create_connection(self, authenticated_client, workflow):
        """Create a connection between nodes."""
        from apps.workflows.models import Node
        source = Node.objects.create(
            workflow=workflow, type='trigger.manual',
            position_x=0, position_y=0
        )
        target = Node.objects.create(
            workflow=workflow, type='llm.claude',
            position_x=200, position_y=0
        )

        url = reverse('workflows:workflow-connections-list', kwargs={'workflow_pk': workflow.id})
        response = authenticated_client.post(
            url,
            {
                'source_node_id': str(source.id),
                'source_port': 'trigger',
                'target_node_id': str(target.id),
                'target_port': 'prompt'
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_connect_node_to_itself(self, authenticated_client, workflow, node):
        """Cannot create a connection from a node to itself."""
        url = reverse('workflows:workflow-connections-list', kwargs={'workflow_pk': workflow.id})
        response = authenticated_client.post(
            url,
            {
                'source_node_id': str(node.id),
                'source_port': 'output',
                'target_node_id': str(node.id),
                'target_port': 'input'
            },
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
