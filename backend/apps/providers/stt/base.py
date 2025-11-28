"""
Base STT Provider interface.

All STT providers implement this interface for speech-to-text transcription.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
from datetime import datetime


@dataclass
class TranscriptSegment:
    """A segment of transcribed speech."""
    text: str
    start_time: float = 0.0  # seconds
    end_time: float = 0.0
    confidence: float = 1.0
    speaker: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'confidence': self.confidence,
            'speaker': self.speaker,
        }


@dataclass
class STTRequest:
    """Request for STT transcription."""
    # Audio data (bytes) or file path
    audio_data: Optional[bytes] = None
    audio_path: Optional[str] = None

    # Audio format info
    sample_rate: int = 16000
    channels: int = 1
    format: str = 'wav'  # 'wav', 'mp3', 'webm', 'raw'

    # Options
    language: str = 'en'
    enable_timestamps: bool = False
    enable_word_timestamps: bool = False


@dataclass
class STTResponse:
    """Response from STT provider."""
    text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: str = 'en'
    confidence: float = 1.0
    duration_seconds: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'segments': [s.to_dict() for s in self.segments],
            'language': self.language,
            'confidence': self.confidence,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat(),
        }


class BaseSTTProvider(ABC):
    """
    Abstract base class for STT providers.

    Implementations must provide:
    - transcribe(): Synchronous transcription
    - transcribe_async(): Asynchronous transcription
    - transcribe_stream(): Real-time streaming transcription
    - list_languages(): List supported languages
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
        """Provider name (e.g., 'vosk', 'whisper')."""
        pass

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports real-time streaming."""
        return False

    @property
    def supports_diarization(self) -> bool:
        """Whether this provider supports speaker diarization."""
        return False

    @abstractmethod
    def transcribe(self, request: STTRequest) -> STTResponse:
        """
        Transcribe audio synchronously.

        Args:
            request: STT request with audio data

        Returns:
            STTResponse with transcribed text
        """
        pass

    @abstractmethod
    async def transcribe_async(self, request: STTRequest) -> STTResponse:
        """
        Transcribe audio asynchronously.
        """
        pass

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
        language: str = 'en',
        callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[TranscriptSegment]:
        """
        Transcribe audio stream in real-time.

        Args:
            audio_stream: Async iterator of audio chunks
            sample_rate: Audio sample rate
            language: Language code
            callback: Optional callback for partial results

        Yields:
            TranscriptSegment for each recognized utterance
        """
        raise NotImplementedError(
            f"{self.name} provider does not support streaming transcription"
        )

    @abstractmethod
    def list_languages(self) -> List[str]:
        """
        List supported languages.

        Returns:
            List of language codes
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider is responding
        """
        pass

    def clean_transcript(self, text: str) -> str:
        """
        Clean transcribed text.

        Override to customize post-processing.
        """
        import re
        # Remove filler words if needed
        text = text.strip()
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text
