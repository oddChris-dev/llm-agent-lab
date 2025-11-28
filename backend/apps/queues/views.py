"""
Views for queue management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Queue, QueueItem


class QueueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for queue CRUD operations.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Queue.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='items')
    def enqueue(self, request, pk=None):
        """
        Add an item to the queue.
        """
        queue = self.get_object()
        item = QueueItem.objects.create(
            queue=queue,
            data=request.data.get('data', {}),
            priority=request.data.get('priority', 0)
        )
        return Response({
            'id': str(item.id),
            'status': item.status
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def dequeue(self, request, pk=None):
        """
        Get next item from the queue.
        """
        queue = self.get_object()
        item = QueueItem.objects.filter(
            queue=queue,
            status='pending'
        ).order_by('-priority', 'created_at').first()

        if not item:
            return Response({'item': None})

        item.status = 'processing'
        item.save()

        return Response({
            'id': str(item.id),
            'data': item.data
        })
