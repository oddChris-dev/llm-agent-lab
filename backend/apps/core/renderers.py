"""
Custom renderers for consistent API response format.
"""

import uuid
from datetime import datetime
from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that wraps responses in standard format.

    Success responses:
    {
        "data": { ... },
        "meta": {
            "request_id": "...",
            "timestamp": "..."
        }
    }

    Error responses are handled by the exception handler.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None

        # Don't wrap if already wrapped or if it's an error
        if isinstance(data, dict):
            if 'data' in data or 'error' in data:
                # Already in standard format
                return super().render(data, accepted_media_type, renderer_context)

        # Don't wrap error responses (handled by exception handler)
        if response and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        # Wrap successful responses
        wrapped_data = {
            'data': data,
            'meta': {
                'request_id': str(uuid.uuid4())[:8],
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
        }

        return super().render(wrapped_data, accepted_media_type, renderer_context)
