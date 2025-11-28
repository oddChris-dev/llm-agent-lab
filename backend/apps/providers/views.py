"""
Views for provider management.
"""

import time
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models

from .models import Provider, ProviderType
from .serializers import ProviderSerializer, ProviderCreateSerializer

logger = logging.getLogger(__name__)


class ProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider CRUD operations.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Provider.objects.filter(
            models.Q(user=self.request.user) | models.Q(is_system=True)
        )
        provider_type = self.request.query_params.get('type')
        if provider_type:
            queryset = queryset.filter(type=provider_type)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ProviderCreateSerializer
        return ProviderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test provider connection by calling the health check endpoint.
        """
        provider = self.get_object()
        config = provider.config or {}

        start_time = time.time()

        try:
            success, message, models_list = self._test_provider(provider.type, config)
            latency_ms = int((time.time() - start_time) * 1000)

            return Response({
                'success': success,
                'latency_ms': latency_ms,
                'message': message,
                'models': models_list
            })
        except Exception as e:
            logger.exception(f"Provider test failed: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            return Response({
                'success': False,
                'latency_ms': latency_ms,
                'message': str(e),
                'models': []
            })

    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        """
        List available models for this provider.
        """
        provider = self.get_object()
        config = provider.config or {}

        try:
            models_list = self._get_provider_models(provider.type, config)
            return Response({'models': models_list})
        except Exception as e:
            logger.exception(f"Failed to get models: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _test_provider(self, provider_type: str, config: dict) -> tuple:
        """
        Test provider connection and return (success, message, models).
        """
        if provider_type == ProviderType.LLM:
            return self._test_llm_provider(config)
        elif provider_type == ProviderType.TTS:
            return self._test_tts_provider(config)
        elif provider_type == ProviderType.STT:
            return self._test_stt_provider(config)
        elif provider_type == ProviderType.IMAGE:
            return self._test_image_provider(config)
        else:
            return False, 'Unknown provider type', []

    def _test_llm_provider(self, config: dict) -> tuple:
        """Test LLM provider connection."""
        llm_type = config.get('type', 'ollama')

        if llm_type == 'ollama':
            from .llm.ollama import OllamaProvider
            provider = OllamaProvider(config)
            if provider.health_check():
                models = provider.list_models()
                return True, f'Connected. {len(models)} models available.', models
            return False, 'Ollama server not responding', []

        elif llm_type == 'anthropic':
            from .llm.anthropic import AnthropicProvider
            try:
                provider = AnthropicProvider(config)
                if provider.health_check():
                    models = provider.list_models()
                    return True, f'Connected to Anthropic API.', models
                return False, 'Anthropic API not responding', []
            except ValueError as e:
                return False, str(e), []

        elif llm_type == 'openai':
            # OpenAI support placeholder
            return False, 'OpenAI provider not yet implemented', []

        return False, f'Unknown LLM type: {llm_type}', []

    def _test_tts_provider(self, config: dict) -> tuple:
        """Test TTS provider connection."""
        tts_type = config.get('type', 'xtts')

        if tts_type == 'xtts':
            try:
                from .tts.xtts import XTTSProvider
                provider = XTTSProvider(config)
                if provider.health_check():
                    return True, 'XTTS server connected', []
                return False, 'XTTS server not responding', []
            except ImportError:
                return False, 'XTTS provider not installed', []

        return False, f'Unknown TTS type: {tts_type}', []

    def _test_stt_provider(self, config: dict) -> tuple:
        """Test STT provider connection."""
        stt_type = config.get('type', 'vosk')

        if stt_type == 'vosk':
            return True, 'Vosk is a local provider (no connection test needed)', []

        return False, f'Unknown STT type: {stt_type}', []

    def _test_image_provider(self, config: dict) -> tuple:
        """Test image provider connection."""
        img_type = config.get('type', 'comfyui')

        if img_type == 'comfyui':
            import httpx
            base_url = config.get('base_url', 'http://localhost:8188')
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f'{base_url}/system_stats')
                    if response.status_code == 200:
                        return True, 'ComfyUI server connected', []
            except Exception:
                pass
            return False, 'ComfyUI server not responding', []

        return False, f'Unknown image type: {img_type}', []

    def _get_provider_models(self, provider_type: str, config: dict) -> list:
        """Get available models for a provider."""
        if provider_type == ProviderType.LLM:
            llm_type = config.get('type', 'ollama')

            if llm_type == 'ollama':
                from .llm.ollama import OllamaProvider
                provider = OllamaProvider(config)
                return provider.list_models()

            elif llm_type == 'anthropic':
                from .llm.anthropic import AnthropicProvider
                provider = AnthropicProvider(config)
                return provider.list_models()

        return []
