"""
Serializers for queue models.
"""

from rest_framework import serializers
from .models import Queue, QueueItem, QueueStrategy, QueueItemStatus


class QueueItemSerializer(serializers.ModelSerializer):
    """Serializer for queue items."""

    class Meta:
        model = QueueItem
        fields = [
            'id', 'data', 'priority', 'status',
            'attempts', 'max_attempts', 'last_error',
            'available_at', 'expires_at',
            'processing_started_at', 'processed_at',
            'source_execution_id', 'source_node_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'attempts', 'last_error',
            'processing_started_at', 'processed_at',
            'created_at', 'updated_at'
        ]


class QueueItemCreateSerializer(serializers.Serializer):
    """Serializer for creating queue items."""
    data = serializers.JSONField()
    priority = serializers.IntegerField(default=0)
    delay_seconds = serializers.IntegerField(default=0, min_value=0)
    source_execution_id = serializers.UUIDField(required=False, allow_null=True)
    source_node_id = serializers.UUIDField(required=False, allow_null=True)


class QueueItemBatchCreateSerializer(serializers.Serializer):
    """Serializer for batch creating queue items."""
    items = QueueItemCreateSerializer(many=True)


class QueueSerializer(serializers.ModelSerializer):
    """Serializer for queue list."""
    pending_count = serializers.SerializerMethodField()
    processing_count = serializers.SerializerMethodField()

    class Meta:
        model = Queue
        fields = [
            'id', 'name', 'slug', 'description',
            'strategy', 'config',
            'max_size', 'item_ttl_seconds',
            'pending_count', 'processing_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_pending_count(self, obj):
        return obj.items.filter(status=QueueItemStatus.PENDING).count()

    def get_processing_count(self, obj):
        return obj.items.filter(status=QueueItemStatus.PROCESSING).count()


class QueueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating queues."""

    class Meta:
        model = Queue
        fields = [
            'name', 'slug', 'description',
            'strategy', 'config',
            'max_size', 'item_ttl_seconds',
            'workflow'
        ]

    def validate_strategy(self, value):
        if value not in QueueStrategy.values:
            raise serializers.ValidationError(
                f"Invalid strategy. Must be one of: {', '.join(QueueStrategy.values)}"
            )
        return value


class QueueDetailSerializer(QueueSerializer):
    """Detailed serializer for queue with stats."""
    completed_count = serializers.SerializerMethodField()
    failed_count = serializers.SerializerMethodField()
    expired_count = serializers.SerializerMethodField()
    recent_items = serializers.SerializerMethodField()

    class Meta(QueueSerializer.Meta):
        fields = QueueSerializer.Meta.fields + [
            'completed_count', 'failed_count', 'expired_count',
            'recent_items'
        ]

    def get_completed_count(self, obj):
        return obj.items.filter(status=QueueItemStatus.COMPLETED).count()

    def get_failed_count(self, obj):
        return obj.items.filter(status=QueueItemStatus.FAILED).count()

    def get_expired_count(self, obj):
        return obj.items.filter(status=QueueItemStatus.EXPIRED).count()

    def get_recent_items(self, obj):
        items = obj.items.all()[:10]
        return QueueItemSerializer(items, many=True).data


class DequeueSerializer(serializers.Serializer):
    """Serializer for dequeue requests."""
    consumer_id = serializers.CharField(required=False, allow_blank=True)


class CompleteItemSerializer(serializers.Serializer):
    """Serializer for completing items."""
    pass


class FailItemSerializer(serializers.Serializer):
    """Serializer for failing items."""
    error = serializers.CharField(required=False, allow_blank=True, default='')


class RequeueItemSerializer(serializers.Serializer):
    """Serializer for requeuing items."""
    delay_seconds = serializers.IntegerField(default=0, min_value=0)
