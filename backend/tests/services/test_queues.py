"""
Unit tests for queue services.
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch
from django.utils import timezone

from apps.queues.models import Queue, QueueItem, QueueStrategy, QueueItemStatus
from apps.queues.services import QueueService, BroadcastQueueService, QueueFullError


@pytest.fixture
def user(db):
    """Create a test user."""
    from django.contrib.auth.models import User
    return User.objects.create_user('testuser', 'test@test.com', 'pass')


@pytest.fixture
def fifo_queue(user):
    """Create a FIFO queue."""
    return Queue.objects.create(
        name='Test FIFO Queue',
        user=user,
        strategy=QueueStrategy.FIFO,
        max_size=100
    )


@pytest.fixture
def lifo_queue(user):
    """Create a LIFO queue."""
    return Queue.objects.create(
        name='Test LIFO Queue',
        user=user,
        strategy=QueueStrategy.LIFO
    )


@pytest.fixture
def priority_queue(user):
    """Create a priority queue."""
    return Queue.objects.create(
        name='Test Priority Queue',
        user=user,
        strategy=QueueStrategy.PRIORITY
    )


@pytest.fixture
def broadcast_queue(user):
    """Create a broadcast queue."""
    return Queue.objects.create(
        name='Test Broadcast Queue',
        user=user,
        strategy=QueueStrategy.BROADCAST
    )


@pytest.mark.django_db
class TestQueueService:
    """Tests for QueueService."""

    def test_push_item(self, fifo_queue):
        """Push an item onto the queue."""
        service = QueueService(fifo_queue)
        item = service.push(data={'message': 'Hello'})

        assert item.queue == fifo_queue
        assert item.data == {'message': 'Hello'}
        assert item.status == QueueItemStatus.PENDING
        assert item.priority == 0

    def test_push_with_priority(self, priority_queue):
        """Push item with priority."""
        service = QueueService(priority_queue)
        item = service.push(data={'task': 'important'}, priority=10)

        assert item.priority == 10

    def test_push_with_delay(self, fifo_queue):
        """Push item with delay."""
        service = QueueService(fifo_queue)
        item = service.push(data={'message': 'delayed'}, delay_seconds=60)

        assert item.available_at is not None
        assert item.available_at > timezone.now()

    def test_push_to_full_queue_raises(self, user):
        """Push to full queue raises QueueFullError."""
        small_queue = Queue.objects.create(
            name='Small Queue',
            user=user,
            strategy=QueueStrategy.FIFO,
            max_size=2
        )
        service = QueueService(small_queue)

        service.push(data={'item': 1})
        service.push(data={'item': 2})

        with pytest.raises(QueueFullError):
            service.push(data={'item': 3})

    def test_push_batch(self, fifo_queue):
        """Push multiple items in batch."""
        service = QueueService(fifo_queue)
        items = service.push_batch([
            {'data': {'n': 1}},
            {'data': {'n': 2}},
            {'data': {'n': 3}, 'priority': 5}
        ])

        assert len(items) == 3
        assert fifo_queue.items.count() == 3

    def test_pop_fifo_order(self, fifo_queue):
        """Pop returns items in FIFO order."""
        service = QueueService(fifo_queue)
        service.push(data={'order': 1})
        service.push(data={'order': 2})
        service.push(data={'order': 3})

        item1 = service.pop()
        item2 = service.pop()

        assert item1.data['order'] == 1
        assert item2.data['order'] == 2
        assert item1.status == QueueItemStatus.PROCESSING

    def test_pop_lifo_order(self, lifo_queue):
        """Pop returns items in LIFO order."""
        service = QueueService(lifo_queue)
        service.push(data={'order': 1})
        service.push(data={'order': 2})
        service.push(data={'order': 3})

        item = service.pop()

        assert item.data['order'] == 3

    def test_pop_priority_order(self, priority_queue):
        """Pop returns items in priority order."""
        service = QueueService(priority_queue)
        service.push(data={'task': 'low'}, priority=1)
        service.push(data={'task': 'high'}, priority=10)
        service.push(data={'task': 'medium'}, priority=5)

        item = service.pop()

        assert item.data['task'] == 'high'
        assert item.priority == 10

    def test_pop_empty_queue(self, fifo_queue):
        """Pop from empty queue returns None."""
        service = QueueService(fifo_queue)
        item = service.pop()

        assert item is None

    def test_pop_respects_delay(self, fifo_queue):
        """Pop skips items not yet available."""
        service = QueueService(fifo_queue)
        service.push(data={'delayed': True}, delay_seconds=3600)
        service.push(data={'immediate': True})

        item = service.pop()

        assert item.data['immediate'] is True

    def test_pop_with_consumer_id(self, fifo_queue):
        """Pop records consumer ID."""
        service = QueueService(fifo_queue)
        service.push(data={'message': 'test'})

        item = service.pop(consumer_id='worker-1')

        assert item.consumer_id == 'worker-1'

    def test_peek(self, fifo_queue):
        """Peek returns items without modifying status."""
        service = QueueService(fifo_queue)
        service.push(data={'n': 1})
        service.push(data={'n': 2})
        service.push(data={'n': 3})

        items = service.peek(count=2)

        assert len(items) == 2
        for item in items:
            assert item.status == QueueItemStatus.PENDING

    def test_complete_item(self, fifo_queue):
        """Complete marks item as completed."""
        service = QueueService(fifo_queue)
        item = service.push(data={'test': True})
        item = service.pop()

        completed_item = service.complete(item)

        assert completed_item.status == QueueItemStatus.COMPLETED
        assert completed_item.completed_at is not None

    def test_fail_item(self, fifo_queue):
        """Fail marks item as failed with error."""
        service = QueueService(fifo_queue)
        item = service.push(data={'test': True})
        item = service.pop()

        failed_item = service.fail(item, 'Processing error occurred')

        assert failed_item.status == QueueItemStatus.FAILED
        assert failed_item.error == 'Processing error occurred'

    def test_requeue_item(self, fifo_queue):
        """Requeue puts item back in queue."""
        service = QueueService(fifo_queue)
        item = service.push(data={'test': True})
        item = service.pop()
        assert item.status == QueueItemStatus.PROCESSING

        requeued = service.requeue(item)

        assert requeued.status == QueueItemStatus.PENDING
        assert requeued.retry_count == 1

    def test_requeue_with_delay(self, fifo_queue):
        """Requeue with delay sets available_at."""
        service = QueueService(fifo_queue)
        item = service.push(data={'test': True})
        item = service.pop()

        requeued = service.requeue(item, delay_seconds=300)

        assert requeued.available_at > timezone.now()

    def test_clear_pending(self, fifo_queue):
        """Clear removes pending items."""
        service = QueueService(fifo_queue)
        service.push(data={'n': 1})
        service.push(data={'n': 2})
        item3 = service.push(data={'n': 3})
        service.pop()  # Makes one processing

        count = service.clear(status=QueueItemStatus.PENDING)

        assert count == 2
        assert fifo_queue.items.filter(status=QueueItemStatus.PENDING).count() == 0
        # Processing item should remain
        assert fifo_queue.items.filter(status=QueueItemStatus.PROCESSING).count() == 1

    def test_clear_all(self, fifo_queue):
        """Clear without status removes all items."""
        service = QueueService(fifo_queue)
        service.push(data={'n': 1})
        service.push(data={'n': 2})

        count = service.clear()

        assert count == 2
        assert fifo_queue.items.count() == 0


@pytest.mark.django_db
class TestBroadcastQueueService:
    """Tests for BroadcastQueueService."""

    def test_pop_delivers_to_multiple_consumers(self, broadcast_queue):
        """Broadcast delivers same item to different consumers."""
        service = BroadcastQueueService(broadcast_queue)
        service.push(data={'message': 'broadcast'})

        item1 = service.pop(consumer_id='consumer-1')
        item2 = service.pop(consumer_id='consumer-2')
        item3 = service.pop(consumer_id='consumer-1')  # Same consumer again

        # Different consumers get the same item
        assert item1.id == item2.id
        # Same consumer gets None (already received)
        assert item3 is None

    def test_broadcast_tracks_consumers(self, broadcast_queue):
        """Broadcast tracks which consumers received item."""
        service = BroadcastQueueService(broadcast_queue)
        item = service.push(data={'message': 'test'})

        service.pop(consumer_id='worker-a')
        service.pop(consumer_id='worker-b')

        item.refresh_from_db()
        # Check metadata contains consumer info
        assert 'delivered_to' in item.metadata
        assert 'worker-a' in item.metadata['delivered_to']
        assert 'worker-b' in item.metadata['delivered_to']

    def test_broadcast_new_item_available(self, broadcast_queue):
        """New broadcast item available to all consumers."""
        service = BroadcastQueueService(broadcast_queue)

        # First item delivered to consumer-1
        service.push(data={'order': 1})
        item1 = service.pop(consumer_id='consumer-1')
        assert item1 is not None

        # Consumer-1 already got item1, but new item should be available
        service.push(data={'order': 2})
        item2 = service.pop(consumer_id='consumer-1')
        assert item2 is not None
        assert item2.data['order'] == 2


@pytest.mark.django_db
class TestQueueExpiration:
    """Tests for queue item expiration."""

    def test_expired_items_not_returned(self, user):
        """Expired items are skipped during pop."""
        queue = Queue.objects.create(
            name='Expiring Queue',
            user=user,
            strategy=QueueStrategy.FIFO,
            item_ttl_seconds=3600  # 1 hour TTL
        )
        service = QueueService(queue)

        # Create an expired item
        expired_item = QueueItem.objects.create(
            queue=queue,
            data={'expired': True},
            status=QueueItemStatus.PENDING,
            created_at=timezone.now() - timedelta(hours=2)  # Created 2 hours ago
        )

        # Create a fresh item
        fresh_item = service.push(data={'fresh': True})

        # Pop should return fresh item, not expired
        result = service.pop()

        assert result.id == fresh_item.id
        assert result.data['fresh'] is True
