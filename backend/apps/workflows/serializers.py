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


class NodeInputSerializer(serializers.Serializer):
    """
    Serializer for node input data when updating workflows.
    """
    id = serializers.CharField()
    type = serializers.CharField()
    name = serializers.CharField()
    position = serializers.DictField()
    config = serializers.DictField(required=False, default=dict)


class ConnectionInputSerializer(serializers.Serializer):
    """
    Serializer for connection input data when updating workflows.
    """
    id = serializers.CharField()
    source_node_id = serializers.CharField()
    source_port = serializers.CharField()
    target_node_id = serializers.CharField()
    target_port = serializers.CharField()


class WorkflowUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating workflows with nodes and connections.
    """
    nodes = NodeInputSerializer(many=True, required=False, write_only=True)
    connections = ConnectionInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Workflow
        fields = ['name', 'description', 'icon', 'color', 'status', 'canvas_data', 'settings', 'nodes', 'connections']

    def update(self, instance, validated_data):
        nodes_data = validated_data.pop('nodes', None)
        connections_data = validated_data.pop('connections', None)

        # Update basic workflow fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update nodes if provided
        if nodes_data is not None:
            # Get existing node IDs
            existing_node_ids = set(instance.nodes.values_list('id', flat=True))
            new_node_ids = set()

            for node_data in nodes_data:
                node_id = node_data['id']
                position = node_data.get('position', {})

                # Try to find existing node or create new one
                try:
                    from uuid import UUID
                    node = instance.nodes.get(id=UUID(node_id))
                    # Update existing node
                    node.type = node_data['type']
                    node.name = node_data['name']
                    node.position_x = position.get('x', 0)
                    node.position_y = position.get('y', 0)
                    node.config = node_data.get('config', {})
                    node.save()
                    new_node_ids.add(node.id)
                except (Node.DoesNotExist, ValueError):
                    # Create new node with new UUID
                    node = Node.objects.create(
                        workflow=instance,
                        type=node_data['type'],
                        name=node_data['name'],
                        position_x=position.get('x', 0),
                        position_y=position.get('y', 0),
                        config=node_data.get('config', {})
                    )
                    new_node_ids.add(node.id)

            # Delete nodes that are no longer in the list
            nodes_to_delete = existing_node_ids - new_node_ids
            if nodes_to_delete:
                instance.nodes.filter(id__in=nodes_to_delete).delete()

        # Update connections if provided
        if connections_data is not None:
            # Delete all existing connections and recreate
            instance.connections.all().delete()

            for conn_data in connections_data:
                Connection.objects.create(
                    workflow=instance,
                    source_node_id=conn_data['source_node_id'],
                    source_port=conn_data['source_port'],
                    target_node_id=conn_data['target_node_id'],
                    target_port=conn_data['target_port']
                )

        # Increment version
        instance.version += 1
        instance.save()

        return instance


class WorkflowDuplicateSerializer(serializers.Serializer):
    """
    Serializer for duplicating a workflow.
    """
    name = serializers.CharField(max_length=200, required=False)
