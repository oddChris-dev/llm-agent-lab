"""
Serializers for workflow models.
"""

from rest_framework import serializers
from .models import Workflow, Node, Connection, WorkflowStatus


class NodeSerializer(serializers.ModelSerializer):
    """
    Serializer for Node model.
    """
    position = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = [
            'id', 'type', 'name', 'position', 'width', 'height',
            'config', 'inputs_config', 'outputs_config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_position(self, obj):
        return {'x': obj.position_x, 'y': obj.position_y}


class NodeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating nodes.
    """
    position = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = Node
        fields = [
            'type', 'name', 'position', 'width', 'height',
            'config', 'inputs_config', 'outputs_config'
        ]

    def create(self, validated_data):
        position = validated_data.pop('position', {})
        node = Node(
            **validated_data,
            position_x=position.get('x', 0),
            position_y=position.get('y', 0)
        )
        node.save()
        return node


class NodeUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating nodes.
    """
    position = serializers.DictField(required=False)

    class Meta:
        model = Node
        fields = ['name', 'position', 'width', 'height', 'config']

    def update(self, instance, validated_data):
        position = validated_data.pop('position', None)
        if position:
            instance.position_x = position.get('x', instance.position_x)
            instance.position_y = position.get('y', instance.position_y)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class NodeBatchUpdateSerializer(serializers.Serializer):
    """
    Serializer for batch updating multiple nodes.
    """
    id = serializers.UUIDField()
    position = serializers.DictField(required=False)
    config = serializers.DictField(required=False)


class ConnectionSerializer(serializers.ModelSerializer):
    """
    Serializer for Connection model.
    """
    class Meta:
        model = Connection
        fields = [
            'id', 'source_node_id', 'source_port',
            'target_node_id', 'target_port', 'style', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ConnectionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating connections.
    """
    class Meta:
        model = Connection
        fields = ['source_node_id', 'source_port', 'target_node_id', 'target_port', 'style']

    def validate(self, data):
        if data['source_node_id'] == data['target_node_id']:
            raise serializers.ValidationError("Cannot connect a node to itself")
        return data


class WorkflowListSerializer(serializers.ModelSerializer):
    """
    Serializer for workflow list (minimal data).
    """
    node_count = serializers.IntegerField(read_only=True)
    connection_count = serializers.IntegerField(read_only=True)
    last_execution = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'icon', 'color', 'status',
            'is_template', 'node_count', 'connection_count',
            'last_execution', 'created_at', 'updated_at'
        ]

    def get_last_execution(self, obj):
        # Get most recent execution
        last_exec = obj.executions.order_by('-created_at').first()
        if last_exec:
            return {
                'id': str(last_exec.id),
                'status': last_exec.status,
                'finished_at': last_exec.finished_at.isoformat() if last_exec.finished_at else None
            }
        return None


class WorkflowDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for workflow detail (full data with nodes and connections).
    """
    nodes = NodeSerializer(many=True, read_only=True)
    connections = ConnectionSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'icon', 'color', 'status',
            'is_template', 'canvas_data', 'settings', 'version',
            'nodes', 'connections', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']


class WorkflowCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating workflows.
    """
    class Meta:
        model = Workflow
        fields = ['name', 'description', 'icon', 'color', 'status', 'settings']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating workflows.
    """
    class Meta:
        model = Workflow
        fields = ['name', 'description', 'icon', 'color', 'status', 'canvas_data', 'settings']


class WorkflowDuplicateSerializer(serializers.Serializer):
    """
    Serializer for duplicating a workflow.
    """
    name = serializers.CharField(max_length=200, required=False)
