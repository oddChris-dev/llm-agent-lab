"""
Base TTS Provider interface.

All TTS providers implement this interface for text-to-speech synthesis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
import io


@dataclass
class TTSRequest:
    """Request for TTS synthesis."""
    text: str
    voice_id: str
    language: str = 'en'
    speed: float = 1.0
    # Optional voice sample for cloning (as bytes)
    voice_sample: Optional[bytes] = None


@dataclass
class TTSResponse:
    """Response from TTS provider."""
    audio_data: bytes
    sample_rate: int
    format: str = 'wav'  # 'wav', 'mp3', 'ogg'
    duration_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_file(self, path: str) -> None:
        """Write audio data to file."""
        with open(path, 'wb') as f:
            f.write(self.audio_data)

    def to_bytes_io(self) -> io.BytesIO:
        """Get audio data as BytesIO stream."""
        return io.BytesIO(self.audio_data)


@dataclass
class VoiceInfo:
    """Information about an available voice."""
    id: str
    name: str
    language: str
    gender: Optional[str] = None
    description: Optional[str] = None
    sample_url: Optional[str] = None
    # For cloned voices
    is_cloned: bool = False


class BaseTTSProvider(ABC):
    """
    Abstract base class for TTS providers.

    Implementations must provide:
    - synthesize(): Synchronous speech synthesis
    - synthesize_async(): Asynchronous speech synthesis
    - stream(): Streaming synthesis for real-time playback
    - list_voices(): List available voices
    - clone_voice(): Create a cloned voice from sample (if supported)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration dict
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'xtts', 'elevenlabs')."""
        pass

    @property
    def supports_cloning(self) -> bool:
        """Whether this provider supports voice cloning."""
        return False

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming synthesis."""
        return False

    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize speech synchronously.

        Args:
            request: TTS request with text and voice settings

        Returns:
            TTSResponse with audio data
        """
        pass

    @abstractmethod
    async def synthesize_async(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize speech asynchronously.
        """
        pass

    async def stream(self, request: TTSRequest) -> AsyncIterator[bytes]:
        """
        Stream audio chunks for real-time playback.

        Override in providers that support streaming.

        Yields:
            Audio data chunks
        """
        # Default implementation: synthesize full audio and yield in chunks
        response = await self.synthesize_async(request)
        chunk_size = 4096
        audio = response.audio_data
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]

    @abstractmethod
    def list_voices(self) -> List[VoiceInfo]:
        """
        List available voices.

        Returns:
            List of VoiceInfo objects
        """
        pass

    def clone_voice(
        self,
        name: str,
        audio_sample: bytes,
        description: Optional[str] = None
    ) -> VoiceInfo:
        """
        Create a cloned voice from an audio sample.

        Args:
            name: Name for the cloned voice
            audio_sample: Audio data (WAV format preferred)
            description: Optional description

        Returns:
            VoiceInfo for the cloned voice

        Raises:
            NotImplementedError if cloning not supported
        """
        raise NotImplementedError(
            f"{self.name} provider does not support voice cloning"
        )

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider is responding
        """
        pass

    def clean_text(self, text: str) -> str:
        """
        Clean text for TTS synthesis.

        Override to customize text preprocessing.
        """
        import re
        # Remove unsupported characters
        text = re.sub(r'[^\w\s\'%;:,.\-=!?]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def split_text(self, text: str, max_length: int = 200) -> List[str]:
        """
        Split long text into chunks for synthesis.

        Args:
            text: Text to split
            max_length: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        sentences = text.replace('!', '.').replace('?', '.').split('.')

        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += (" " if current_chunk else "") + sentence + "."
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "."

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
