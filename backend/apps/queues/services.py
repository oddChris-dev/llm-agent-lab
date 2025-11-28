"""
Queue service for managing queue operations.

Provides push, pop, peek operations with support for different strategies:
- FIFO: First In, First Out
- LIFO: Last In, First Out
- ROUND_ROBIN: Distribute items across consumers
- BROADCAST: Send to all consumers
- PRIORITY: Priority-based ordering
- CONDITIONAL: Route based on conditions
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Queue, QueueItem, QueueStrategy, QueueItemStatus


class QueueService:
    """Service class for queue operations."""

    def __init__(self, queue: Queue):
        self.queue = queue

    @classmethod
    def get_queue(cls, queue_id: str) -> 'QueueService':
        """Get a queue service by ID."""
        queue = Queue.objects.get(id=queue_id)
        return cls(queue)

    @classmethod
    def get_by_slug(cls, slug: str) -> 'QueueService':
        """Get a queue service by slug."""
        queue = Queue.objects.get(slug=slug)
        return cls(queue)

    def push(
        self,
        data: Any,
        priority: int = 0,
        delay_seconds: int = 0,
        source_execution_id: str = None,
        source_node_id: str = None,
    ) -> QueueItem:
        """
        Push an item onto the queue.

        Args:
            data: The data to queue (will be JSON serialized)
            priority: Priority level (higher = more important)
            delay_seconds: Delay before item becomes available
            source_execution_id: ID of execution that produced this item
            source_node_id: ID of node that produced this item

        Returns:
            The created QueueItem
        """
        # Check queue size limit
        if self.queue.max_size:
            current_size = self.queue.items.filter(
                status__in=[QueueItemStatus.PENDING, QueueItemStatus.PROCESSING]
            ).count()
            if current_size >= self.queue.max_size:
                raise QueueFullError(f"Queue '{self.queue.name}' is full")

        # Calculate availability and expiry
        available_at = timezone.now()
        if delay_seconds > 0:
            available_at += timedelta(seconds=delay_seconds)

        expires_at = None
        if self.queue.item_ttl_seconds:
            expires_at = available_at + timedelta(seconds=self.queue.item_ttl_seconds)

        item = QueueItem.objects.create(
            queue=self.queue,
            data=data,
            priority=priority,
            available_at=available_at,
            expires_at=expires_at,
            source_execution_id=source_execution_id,
            source_node_id=source_node_id,
        )

        return item

    def push_batch(self, items: List[Dict[str, Any]]) -> List[QueueItem]:
        """
        Push multiple items onto the queue.

        Args:
            items: List of dicts with 'data' and optional 'priority', 'delay_seconds'

        Returns:
            List of created QueueItems
        """
        created = []
        for item_data in items:
            item = self.push(
                data=item_data['data'],
                priority=item_data.get('priority', 0),
                delay_seconds=item_data.get('delay_seconds', 0),
                source_execution_id=item_data.get('source_execution_id'),
                source_node_id=item_data.get('source_node_id'),
            )
            created.append(item)
        return created

    @transaction.atomic
    def pop(self, consumer_id: str = None) -> Optional[QueueItem]:
        """
        Pop the next available item from the queue.

        The strategy determines which item is returned:
        - FIFO: Oldest item
        - LIFO: Newest item
        - PRIORITY: Highest priority, then oldest
        - ROUND_ROBIN: Next item for this consumer

        Args:
            consumer_id: Optional consumer identifier for round-robin

        Returns:
            QueueItem or None if queue is empty
        """
        item = self._get_next_item(consumer_id)

        if item:
            item.status = QueueItemStatus.PROCESSING
            item.processing_started_at = timezone.now()
            item.attempts = F('attempts') + 1
            item.save(update_fields=['status', 'processing_started_at', 'attempts'])
            item.refresh_from_db()

        return item

    def peek(self, count: int = 1) -> List[QueueItem]:
        """
        Peek at the next items without removing them.

        Args:
            count: Number of items to peek

        Returns:
            List of QueueItems
        """
        queryset = self._get_available_queryset()
        queryset = self._apply_strategy_ordering(queryset)
        return list(queryset[:count])

    def complete(self, item: QueueItem) -> QueueItem:
        """Mark an item as completed."""
        item.status = QueueItemStatus.COMPLETED
        item.processed_at = timezone.now()
        item.save(update_fields=['status', 'processed_at'])
        return item

    def fail(self, item: QueueItem, error: str = '') -> QueueItem:
        """
        Mark an item as failed.

        If retry attempts remain, item will be made available again.
        """
        item.last_error = error

        if item.attempts < item.max_attempts:
            # Retry with exponential backoff
            delay = min(300, 2 ** item.attempts)  # Max 5 minutes
            item.status = QueueItemStatus.PENDING
            item.available_at = timezone.now() + timedelta(seconds=delay)
        else:
            item.status = QueueItemStatus.FAILED
            item.processed_at = timezone.now()

        item.save(update_fields=['status', 'last_error', 'available_at', 'processed_at'])
        return item

    def requeue(self, item: QueueItem, delay_seconds: int = 0) -> QueueItem:
        """Put a failed/completed item back in the queue."""
        item.status = QueueItemStatus.PENDING
        item.processing_started_at = None
        item.processed_at = None
        item.attempts = 0
        item.last_error = ''

        if delay_seconds > 0:
            item.available_at = timezone.now() + timedelta(seconds=delay_seconds)
        else:
            item.available_at = timezone.now()

        item.save()
        return item

    def size(self, include_processing: bool = False) -> int:
        """Get the number of items in the queue."""
        statuses = [QueueItemStatus.PENDING]
        if include_processing:
            statuses.append(QueueItemStatus.PROCESSING)

        return self.queue.items.filter(status__in=statuses).count()

    def clear(self, status: QueueItemStatus = None) -> int:
        """
        Clear items from the queue.

        Args:
            status: Only clear items with this status (default: all pending)

        Returns:
            Number of items deleted
        """
        queryset = self.queue.items.all()
        if status:
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.filter(status=QueueItemStatus.PENDING)

        count = queryset.count()
        queryset.delete()
        return count

    def cleanup_expired(self) -> int:
        """Remove expired items from the queue."""
        now = timezone.now()
        expired = self.queue.items.filter(
            status=QueueItemStatus.PENDING,
            expires_at__lt=now
        )
        count = expired.count()
        expired.update(status=QueueItemStatus.EXPIRED)
        return count

    def cleanup_stale(self, timeout_seconds: int = 3600) -> int:
        """
        Requeue items stuck in processing state.

        Args:
            timeout_seconds: How long before processing items are considered stale

        Returns:
            Number of items requeued
        """
        cutoff = timezone.now() - timedelta(seconds=timeout_seconds)
        stale = self.queue.items.filter(
            status=QueueItemStatus.PROCESSING,
            processing_started_at__lt=cutoff
        )

        count = stale.count()
        for item in stale:
            self.fail(item, 'Processing timeout')

        return count

    def _get_available_queryset(self):
        """Get queryset of available items."""
        now = timezone.now()
        return self.queue.items.filter(
            status=QueueItemStatus.PENDING,
            available_at__lte=now
        ).exclude(
            expires_at__lt=now
        )

    def _apply_strategy_ordering(self, queryset):
        """Apply ordering based on queue strategy."""
        strategy = self.queue.strategy

        if strategy == QueueStrategy.FIFO:
            return queryset.order_by('created_at')

        elif strategy == QueueStrategy.LIFO:
            return queryset.order_by('-created_at')

        elif strategy == QueueStrategy.PRIORITY:
            return queryset.order_by('-priority', 'created_at')

        elif strategy == QueueStrategy.ROUND_ROBIN:
            # For round robin, we track last consumer in config
            return queryset.order_by('created_at')

        else:
            return queryset.order_by('created_at')

    def _get_next_item(self, consumer_id: str = None) -> Optional[QueueItem]:
        """Get the next item based on strategy."""
        queryset = self._get_available_queryset()
        queryset = self._apply_strategy_ordering(queryset)

        strategy = self.queue.strategy

        if strategy == QueueStrategy.BROADCAST:
            # For broadcast, return item if consumer hasn't seen it
            if consumer_id:
                seen_key = f'seen_by_{consumer_id}'
                queryset = queryset.exclude(
                    **{f'data__{seen_key}': True}
                )

        # Lock and return first available item
        item = queryset.select_for_update(skip_locked=True).first()
        return item


class BroadcastQueueService(QueueService):
    """
    Specialized service for broadcast queues.

    Broadcast queues deliver each item to all registered consumers.
    """

    def __init__(self, queue: Queue):
        super().__init__(queue)
        if queue.strategy != QueueStrategy.BROADCAST:
            raise ValueError("Queue must have BROADCAST strategy")

    def pop(self, consumer_id: str) -> Optional[QueueItem]:
        """
        Get the next unseen item for this consumer.

        Args:
            consumer_id: Required consumer identifier

        Returns:
            QueueItem or None
        """
        if not consumer_id:
            raise ValueError("consumer_id is required for broadcast queues")

        # Get items this consumer hasn't seen
        seen_consumers = self.queue.config.get('seen', {})
        seen_by_consumer = set(seen_consumers.get(consumer_id, []))

        queryset = self._get_available_queryset()
        queryset = queryset.exclude(id__in=seen_by_consumer)
        queryset = queryset.order_by('created_at')

        item = queryset.first()

        if item:
            # Mark as seen by this consumer
            seen_by_consumer.add(str(item.id))
            seen_consumers[consumer_id] = list(seen_by_consumer)
            self.queue.config['seen'] = seen_consumers
            self.queue.save(update_fields=['config'])

        return item

    def register_consumer(self, consumer_id: str):
        """Register a new consumer."""
        consumers = self.queue.config.get('consumers', [])
        if consumer_id not in consumers:
            consumers.append(consumer_id)
            self.queue.config['consumers'] = consumers
            self.queue.save(update_fields=['config'])

    def unregister_consumer(self, consumer_id: str):
        """Unregister a consumer."""
        consumers = self.queue.config.get('consumers', [])
        if consumer_id in consumers:
            consumers.remove(consumer_id)
            self.queue.config['consumers'] = consumers

        # Clean up seen tracking
        seen = self.queue.config.get('seen', {})
        seen.pop(consumer_id, None)
        self.queue.config['seen'] = seen

        self.queue.save(update_fields=['config'])


class ConditionalQueueService(QueueService):
    """
    Specialized service for conditional routing queues.

    Routes items to different output queues based on conditions.
    """

    def __init__(self, queue: Queue):
        super().__init__(queue)
        if queue.strategy != QueueStrategy.CONDITIONAL:
            raise ValueError("Queue must have CONDITIONAL strategy")

    def push(self, data: Any, **kwargs) -> QueueItem:
        """Push and route item based on conditions."""
        item = super().push(data, **kwargs)

        # Evaluate routing conditions
        routes = self.queue.config.get('routes', [])
        for route in routes:
            if self._evaluate_condition(data, route.get('condition', {})):
                target_queue_slug = route.get('target_queue')
                if target_queue_slug:
                    target_service = QueueService.get_by_slug(target_queue_slug)
                    target_service.push(
                        data=data,
                        source_execution_id=kwargs.get('source_execution_id'),
                        source_node_id=kwargs.get('source_node_id'),
                    )
                break

        return item

    def _evaluate_condition(self, data: Any, condition: Dict) -> bool:
        """Evaluate a routing condition against data."""
        if not condition:
            return True

        operator = condition.get('operator', 'eq')
        field = condition.get('field')
        value = condition.get('value')

        if not field:
            return True

        # Get field value from data
        actual = data
        for part in field.split('.'):
            if isinstance(actual, dict):
                actual = actual.get(part)
            else:
                actual = None
                break

        # Compare
        if operator == 'eq':
            return actual == value
        elif operator == 'ne':
            return actual != value
        elif operator == 'gt':
            return actual > value
        elif operator == 'gte':
            return actual >= value
        elif operator == 'lt':
            return actual < value
        elif operator == 'lte':
            return actual <= value
        elif operator == 'contains':
            return value in actual if actual else False
        elif operator == 'in':
            return actual in value if value else False

        return False


class QueueFullError(Exception):
    """Raised when attempting to push to a full queue."""
    pass
