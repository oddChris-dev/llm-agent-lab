"""
Serializers for asset models.
"""

from rest_framework import serializers
from .models import Asset, AssetType


class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer for Asset model listing and detail views.
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'type', 'type_display',
            'file_path', 'file_size', 'mime_type', 'checksum',
            'metadata', 'usage_count', 'last_used_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_path', 'file_size', 'checksum',
            'usage_count', 'last_used_at', 'created_at', 'updated_at'
        ]


class AssetCreateSerializer(serializers.Serializer):
    """
    Serializer for creating assets with file upload.
    """
    name = serializers.CharField(max_length=255, required=False)
    type = serializers.ChoiceField(choices=AssetType.choices, default=AssetType.OTHER)
    file = serializers.FileField(required=True)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate_file(self, value):
        # Limit file size to 100MB
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size exceeds maximum of {max_size // (1024*1024)}MB'
            )
        return value


class AssetUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating asset metadata.
    """
    class Meta:
        model = Asset
        fields = ['name', 'metadata']
