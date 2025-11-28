"""
Serializers for provider models.
"""

from rest_framework import serializers
from .models import Provider


class ProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for Provider model.
    """
    class Meta:
        model = Provider
        fields = [
            'id', 'name', 'slug', 'type', 'status',
            'is_default', 'is_system', 'config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Hide sensitive config values in responses
        if 'config' in data and isinstance(data['config'], dict):
            config = data['config'].copy()
            for key in ['api_key', 'secret', 'password']:
                if key in config:
                    config[key] = '***'
            data['config'] = config
        return data


class ProviderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating providers.
    """
    class Meta:
        model = Provider
        fields = ['name', 'slug', 'type', 'config', 'is_default']
