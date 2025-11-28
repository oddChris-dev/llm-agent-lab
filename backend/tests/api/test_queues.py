"""
API tests for queue endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.queues.models import Queue, QueueItem, QueueStrategy, QueueItemStatus


@pytest.fixture
def queue(user):
    """Create a test queue."""
    return Queue.objects.create(
        name='Test Queue',
        user=user,
        strategy=QueueStrategy.FIFO
    )


@pytest.fixture
def queue_with_items(queue):
    """Create queue with some items."""
    QueueItem.objects.create(queue=queue, data={'n': 1})
    QueueItem.objects.create(queue=queue, data={'n': 2})
    QueueItem.objects.create(queue=queue, data={'n': 3})
    return queue


@pytest.mark.django_db
class TestQueueAPI:
    """Test queue CRUD operations."""

    def test_list_queues_unauthenticated(self, api_client):
        """Unauthenticated requests should return 401."""
        url = reverse('queues:queue-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_queues_empty(self, authenticated_client):
        """List queues returns empty when none exist."""
        url = reverse('queues:queue-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    def test_list_queues(self, authenticated_client, queue):
        """List queues returns user's queues."""
        url = reverse('queues:queue-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_queue(self, authenticated_client):
        """Create a new queue."""
        url = reverse('queues:queue-list')
        response = authenticated_client.post(url, {
            'name': 'New Queue',
            'strategy': 'fifo',
            'max_size': 1000
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Queue.objects.count() == 1
        assert Queue.objects.first().name == 'New Queue'

    def test_get_queue_detail(self, authenticated_client, queue):
        """Get queue detail."""
        url = reverse('queues:queue-detail', kwargs={'pk': queue.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == queue.name

    def test_update_queue(self, authenticated_client, queue):
        """Update queue."""
        url = reverse('queues:queue-detail', kwargs={'pk': queue.id})
        response = authenticated_client.patch(url, {
            'name': 'Updated Queue Name'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        queue.refresh_from_db()
        assert queue.name == 'Updated Queue Name'

    def test_delete_queue(self, authenticated_client, queue):
        """Delete queue."""
        url = reverse('queues:queue-detail', kwargs={'pk': queue.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Queue.objects.count() == 0


@pytest.mark.django_db
class TestQueueOperationsAPI:
    """Test queue push/pop operations."""

    def test_push_item(self, authenticated_client, queue):
        """Push item to queue."""
        url = reverse('queues:queue-push', kwargs={'pk': queue.id})
        response = authenticated_client.post(url, {
            'data': {'message': 'Hello'},
            'priority': 5
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data'] == {'message': 'Hello'}
        assert response.data['priority'] == 5

    def test_push_batch(self, authenticated_client, queue):
        """Push batch of items."""
        url = reverse('queues:queue-push-batch', kwargs={'pk': queue.id})
        response = authenticated_client.post(url, {
            'items': [
                {'data': {'n': 1}},
                {'data': {'n': 2}, 'priority': 10},
                {'data': {'n': 3}}
            ]
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 3
        assert queue.items.count() == 3

    def test_pop_item(self, authenticated_client, queue_with_items):
        """Pop item from queue."""
        url = reverse('queues:queue-pop', kwargs={'pk': queue_with_items.id})
        response = authenticated_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['item'] is not None
        assert response.data['item']['data']['n'] == 1

    def test_pop_empty_queue(self, authenticated_client, queue):
        """Pop from empty queue returns null item."""
        url = reverse('queues:queue-pop', kwargs={'pk': queue.id})
        response = authenticated_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['item'] is None

    def test_pop_with_consumer_id(self, authenticated_client, queue_with_items):
        """Pop with consumer ID."""
        url = reverse('queues:queue-pop', kwargs={'pk': queue_with_items.id})
        response = authenticated_client.post(url, {
            'consumer_id': 'worker-1'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        item = QueueItem.objects.get(id=response.data['item']['id'])
        assert item.consumer_id == 'worker-1'

    def test_peek_items(self, authenticated_client, queue_with_items):
        """Peek at items without removing."""
        url = reverse('queues:queue-peek', kwargs={'pk': queue_with_items.id})
        response = authenticated_client.get(url + '?count=2')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 2
        # Items should still be pending
        assert queue_with_items.items.filter(status=QueueItemStatus.PENDING).count() == 3

    def test_clear_queue(self, authenticated_client, queue_with_items):
        """Clear queue items."""
        url = reverse('queues:queue-clear', kwargs={'pk': queue_with_items.id})
        response = authenticated_client.post(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cleared'] == 3
        assert queue_with_items.items.count() == 0

    def test_queue_stats(self, authenticated_client, queue_with_items):
        """Get queue statistics."""
        # Pop one item to make it processing
        service_url = reverse('queues:queue-pop', kwargs={'pk': queue_with_items.id})
        authenticated_client.post(service_url, {}, format='json')

        url = reverse('queues:queue-stats', kwargs={'pk': queue_with_items.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 3
        assert response.data['pending'] == 2
        assert response.data['processing'] == 1


@pytest.mark.django_db
class TestQueueItemAPI:
    """Test queue item operations."""

    def test_complete_item(self, authenticated_client, queue_with_items):
        """Mark item as complete."""
        # Pop item first
        pop_url = reverse('queues:queue-pop', kwargs={'pk': queue_with_items.id})
        pop_response = authenticated_client.post(pop_url, {}, format='json')
        item_id = pop_response.data['item']['id']

        url = reverse(
            'queues:queue-items-complete',
            kwargs={'queue_pk': queue_with_items.id, 'pk': item_id}
        )
        response = authenticated_client.post(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'

    def test_fail_item(self, authenticated_client, queue_with_items):
        """Mark item as failed."""
        # Pop item first
        pop_url = reverse('queues:queue-pop', kwargs={'pk': queue_with_items.id})
        pop_response = authenticated_client.post(pop_url, {}, format='json')
        item_id = pop_response.data['item']['id']

        url = reverse(
            'queues:queue-items-fail',
            kwargs={'queue_pk': queue_with_items.id, 'pk': item_id}
        )
        response = authenticated_client.post(url, {
            'error': 'Processing failed'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'failed'
        assert response.data['error'] == 'Processing failed'

    def test_requeue_item(self, authenticated_client, queue_with_items):
        """Requeue an item."""
        # Pop item first
        pop_url = reverse('queues:queue-pop', kwargs={'pk': queue_with_items.id})
        pop_response = authenticated_client.post(pop_url, {}, format='json')
        item_id = pop_response.data['item']['id']

        url = reverse(
            'queues:queue-items-requeue',
            kwargs={'queue_pk': queue_with_items.id, 'pk': item_id}
        )
        response = authenticated_client.post(url, {
            'delay_seconds': 60
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'pending'
        assert response.data['retry_count'] == 1
