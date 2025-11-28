"""
Custom pagination classes for LLM Agent Lab API.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination with customizable page size.

    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
    """
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        Return paginated response with standard metadata format.
        """
        return Response({
            'data': data,
            'meta': {
                'pagination': {
                    'page': self.page.number,
                    'per_page': self.get_page_size(self.request),
                    'total_pages': self.page.paginator.num_pages,
                    'total_count': self.page.paginator.count,
                    'has_next': self.page.has_next(),
                    'has_prev': self.page.has_previous(),
                }
            }
        })

    def get_paginated_response_schema(self, schema):
        """Schema for OpenAPI documentation."""
        return {
            'type': 'object',
            'properties': {
                'data': schema,
                'meta': {
                    'type': 'object',
                    'properties': {
                        'pagination': {
                            'type': 'object',
                            'properties': {
                                'page': {'type': 'integer'},
                                'per_page': {'type': 'integer'},
                                'total_pages': {'type': 'integer'},
                                'total_count': {'type': 'integer'},
                                'has_next': {'type': 'boolean'},
                                'has_prev': {'type': 'boolean'},
                            }
                        }
                    }
                }
            }
        }


class LargePagination(StandardPagination):
    """
    Pagination for endpoints that may return large datasets.
    Allows up to 500 items per page.
    """
    page_size = 50
    max_page_size = 500


class NoPagination(PageNumberPagination):
    """
    No pagination - returns all results.
    Use sparingly for small, bounded datasets.
    """
    page_size = None
