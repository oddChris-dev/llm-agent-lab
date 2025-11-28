"""
Views for queue management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Queue, QueueItem, QueueStrategy, QueueItemStatus
from .serializers import (
    QueueSerializer,
    QueueCreateSerializer,
    QueueDetailSerializer,
    QueueItemSerializer,
    QueueItemCreateSerializer,
    QueueItemBatchCreateSerializer,
    DequeueSerializer,
    CompleteItemSerializer,
    FailItemSerializer,
    RequeueItemSerializer,
)
from .services import QueueService, BroadcastQueueService, QueueFullError


class QueueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for queue CRUD operations.

    Endpoints:
    - GET /queues/ - List queues
    - POST /queues/ - Create queue
    - GET /queues/{id}/ - Get queue details
    - PUT /queues/{id}/ - Update queue
    - DELETE /queues/{id}/ - Delete queue
    - POST /queues/{id}/push/ - Push item to queue
    - POST /queues/{id}/push_batch/ - Push multiple items
    - POST /queues/{id}/pop/ - Pop item from queue
    - GET /queues/{id}/peek/ - Peek at next items
    - POST /queues/{id}/clear/ - Clear queue
    - GET /queues/{id}/stats/ - Get queue statistics
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Queue.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return QueueCreateSerializer
        elif self.action == 'retrieve':
            return QueueDetailSerializer
        return QueueSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _get_service(self, queue: Queue) -> QueueService:
        """Get appropriate service for queue strategy."""
        if queue.strategy == QueueStrategy.BROADCAST:
            return BroadcastQueueService(queue)
        return QueueService(queue)

    @action(detail=True, methods=['post'])
    def push(self, request, pk=None):
        """
        Push an item onto the queue.

        Request body:
        {
            "data": {...},
            "priority": 0,
            "delay_seconds": 0
        }
        """
        queue = self.get_object()
        serializer = QueueItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = self._get_service(queue)

        try:
            item = service.push(**serializer.validated_data)
            return Response(
                QueueItemSerializer(item).data,
                status=status.HTTP_201_CREATED
            )
        except QueueFullError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    @action(detail=True, methods=['post'])
    def push_batch(self, request, pk=None):
        """
        Push multiple items onto the queue.

        Request body:
        {
            "items": [
                {"data": {...}, "priority": 0},
                {"data": {...}, "priority": 1}
            ]
        }
        """
        queue = self.get_object()
        serializer = QueueItemBatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = self._get_service(queue)

        try:
            items = service.push_batch(serializer.validated_data['items'])
            return Response(
                QueueItemSerializer(items, many=True).data,
                status=status.HTTP_201_CREATED
            )
        except QueueFullError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    @action(detail=True, methods=['post'])
    def pop(self, request, pk=None):
        """
        Pop the next item from the queue.

        Request body (optional):
        {
            "consumer_id": "my-consumer"
        }
        """
        queue = self.get_object()
        serializer = DequeueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = self._get_service(queue)
        consumer_id = serializer.validated_data.get('consumer_id')

        item = service.pop(consumer_id)

        if not item:
            return Response({'item': None})

        return Response({
            'item': QueueItemSerializer(item).data
        })

    @action(detail=True, methods=['get'])
    def peek(self, request, pk=None):
        """
        Peek at the next items without removing them.

        Query params:
        - count: Number of items to peek (default: 5, max: 100)
        """
        queue = self.get_object()
        count = min(int(request.query_params.get('count', 5)), 100)

        service = self._get_service(queue)
        items = service.peek(count)

        return Response({
            'items': QueueItemSerializer(items, many=True).data
        })

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """
        Clear items from the queue.

        Query params:
        - status: Only clear items with this status (default: pending)
        """
        queue = self.get_object()
        item_status = request.query_params.get('status')

        if item_status and item_status not in QueueItemStatus.values:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(QueueItemStatus.values)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = self._get_service(queue)
        count = service.clear(item_status)

        return Response({'cleared': count})

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get queue statistics."""
        queue = self.get_object()
        items = queue.items.all()

        return Response({
            'total': items.count(),
            'pending': items.filter(status=QueueItemStatus.PENDING).count(),
            'processing': items.filter(status=QueueItemStatus.PROCESSING).count(),
            'completed': items.filter(status=QueueItemStatus.COMPLETED).count(),
            'failed': items.filter(status=QueueItemStatus.FAILED).count(),
            'expired': items.filter(status=QueueItemStatus.EXPIRED).count(),
            'strategy': queue.strategy,
            'max_size': queue.max_size,
            'item_ttl_seconds': queue.item_ttl_seconds,
        })

    # Legacy endpoints for backwards compatibility
    @action(detail=True, methods=['post'], url_path='items')
    def enqueue(self, request, pk=None):
        """Legacy: Add an item to the queue."""
        return self.push(request, pk)

    @action(detail=True, methods=['post'], url_path='dequeue')
    def dequeue(self, request, pk=None):
        """Legacy: Get next item from the queue."""
        return self.pop(request, pk)


class QueueItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for queue item operations.

    Nested under queues: /queues/{queue_id}/items/

    Endpoints:
    - GET /queues/{queue_id}/items/ - List items
    - GET /queues/{queue_id}/items/{id}/ - Get item
    - POST /queues/{queue_id}/items/{id}/complete/ - Mark complete
    - POST /queues/{queue_id}/items/{id}/fail/ - Mark failed
    - POST /queues/{queue_id}/items/{id}/requeue/ - Requeue item
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QueueItemSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        queue_id = self.kwargs.get('queue_pk')
        return QueueItem.objects.filter(
            queue_id=queue_id,
            queue__user=self.request.user
        )

    def _get_service(self) -> QueueService:
        """Get queue service for the current queue."""
        queue_id = self.kwargs.get('queue_pk')
        queue = get_object_or_404(Queue, id=queue_id, user=self.request.user)

        if queue.strategy == QueueStrategy.BROADCAST:
            return BroadcastQueueService(queue)
        return QueueService(queue)

    @action(detail=True, methods=['post'])
    def complete(self, request, queue_pk=None, pk=None):
        """Mark an item as completed."""
        item = self.get_object()
        service = self._get_service()

        item = service.complete(item)
        return Response(QueueItemSerializer(item).data)

    @action(detail=True, methods=['post'])
    def fail(self, request, queue_pk=None, pk=None):
        """Mark an item as failed."""
        item = self.get_object()
        serializer = FailItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = self._get_service()
        item = service.fail(item, serializer.validated_data.get('error', ''))

        return Response(QueueItemSerializer(item).data)

    @action(detail=True, methods=['post'])
    def requeue(self, request, queue_pk=None, pk=None):
        """Put an item back in the queue."""
        item = self.get_object()
        serializer = RequeueItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = self._get_service()
        item = service.requeue(item, serializer.validated_data.get('delay_seconds', 0))

        return Response(QueueItemSerializer(item).data)
