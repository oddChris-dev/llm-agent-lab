"""
Custom exception handling for consistent API error responses.
"""

import uuid
import logging
from datetime import datetime
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

logger = logging.getLogger(__name__)


class APIError(APIException):
    """
    Base exception for custom API errors.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'INTERNAL_ERROR'
    default_detail = 'An unexpected error occurred.'

    def __init__(self, detail=None, code=None, status_code=None):
        if detail is not None:
            self.detail = detail
        else:
            self.detail = self.default_detail

        if code is not None:
            self.code = code
        else:
            self.code = self.default_code

        if status_code is not None:
            self.status_code = status_code


class NotFoundError(APIError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'NOT_FOUND'
    default_detail = 'The requested resource was not found.'


class ValidationError(APIError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'VALIDATION_ERROR'
    default_detail = 'Invalid request parameters.'


class ConflictError(APIError):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'CONFLICT'
    default_detail = 'Resource conflict.'


class ProviderError(APIError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = 'PROVIDER_ERROR'
    default_detail = 'External provider error.'


class ExecutionError(APIError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'EXECUTION_ERROR'
    default_detail = 'Workflow execution failed.'


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error format.

    Response format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": { ... }  # Optional
        },
        "meta": {
            "request_id": "...",
            "timestamp": "..."
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Generate request ID for tracking
    request_id = str(uuid.uuid4())[:8]

    # Log the error
    logger.error(
        f"API Error [{request_id}]: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={'request_id': request_id}
    )

    if response is not None:
        # Extract error details
        if isinstance(exc, APIError):
            error_code = exc.code
            error_message = str(exc.detail)
            error_details = None
        elif isinstance(exc, Http404):
            error_code = 'NOT_FOUND'
            error_message = 'The requested resource was not found.'
            error_details = None
        else:
            error_code = getattr(exc, 'default_code', 'ERROR').upper()
            error_message = _get_error_message(exc)
            error_details = _get_error_details(exc, response.data)

        # Build standardized error response
        response.data = {
            'error': {
                'code': error_code,
                'message': error_message,
            },
            'meta': {
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
        }

        if error_details:
            response.data['error']['details'] = error_details

    return response


def _get_error_message(exc):
    """Extract a human-readable error message from an exception."""
    if hasattr(exc, 'detail'):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        elif isinstance(detail, list):
            return detail[0] if detail else 'Validation error.'
        elif isinstance(detail, dict):
            # Get first error message
            for key, value in detail.items():
                if isinstance(value, list):
                    return f"{key}: {value[0]}"
                return f"{key}: {value}"
    return str(exc)


def _get_error_details(exc, response_data):
    """Extract detailed error information for validation errors."""
    if not isinstance(response_data, dict):
        return None

    details = []
    for field, errors in response_data.items():
        if field in ('detail', 'non_field_errors'):
            continue
        if isinstance(errors, list):
            for error in errors:
                details.append({
                    'field': field,
                    'message': str(error),
                })
        else:
            details.append({
                'field': field,
                'message': str(errors),
            })

    return details if details else None
