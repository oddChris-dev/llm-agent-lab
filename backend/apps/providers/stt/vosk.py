"""
Vosk STT Provider.

Provides integration with Vosk for offline speech recognition.
Vosk is fast, accurate, and works completely offline.
"""

import os
import json
import asyncio
import wave
import io
from typing import List, Optional, AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from .base import (
    BaseSTTProvider,
    STTRequest,
    STTResponse,
    TranscriptSegment,
)


class VoskProvider(BaseSTTProvider):
    """
    Vosk provider for offline speech-to-text.

    Config options:
        model_path: Path to Vosk model directory
        sample_rate: Audio sample rate (default: 16000)
        max_alternatives: Maximum number of alternatives (default: 0)
        words: Include word-level timestamps (default: False)
    """

    # Language codes to model names mapping
    LANGUAGE_MODELS = {
        'en': 'vosk-model-en-us-0.22',
        'en-us': 'vosk-model-en-us-0.22',
        'en-gb': 'vosk-model-en-gb-0.15',
        'es': 'vosk-model-es-0.42',
        'fr': 'vosk-model-fr-0.22',
        'de': 'vosk-model-de-0.21',
        'ru': 'vosk-model-ru-0.42',
        'cn': 'vosk-model-cn-0.22',
        'ja': 'vosk-model-ja-0.22',
        'it': 'vosk-model-it-0.22',
        'pt': 'vosk-model-pt-fb-v0.1.1-20220516_2113',
    }

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.model_path = self.config.get('model_path', 'models/vosk-model-en-us-0.22')
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.max_alternatives = self.config.get('max_alternatives', 0)
        self.include_words = self.config.get('words', False)

        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def name(self) -> str:
        return 'vosk'

    @property
    def supports_streaming(self) -> bool:
        return True

    def _ensure_model_loaded(self):
        """Load model if not already loaded."""
        if self._model is not None:
            return

        try:
            from vosk import Model, SetLogLevel
            SetLogLevel(-1)  # Suppress Vosk logs
        except ImportError:
            raise ImportError(
                "vosk package not installed. Install with: pip install vosk"
            )

        if not os.path.exists(self.model_path):
            raise ValueError(
                f"Vosk model not found at {self.model_path}. "
                f"Download from https://alphacephei.com/vosk/models"
            )

        self._model = Model(self.model_path)

    def _create_recognizer(self, sample_rate: int = None):
        """Create a new recognizer instance."""
        from vosk import KaldiRecognizer

        self._ensure_model_loaded()
        rate = sample_rate or self.sample_rate
        rec = KaldiRecognizer(self._model, rate)

        if self.max_alternatives > 0:
            rec.SetMaxAlternatives(self.max_alternatives)

        if self.include_words:
            rec.SetWords(True)

        return rec

    def _transcribe_sync(self, request: STTRequest) -> STTResponse:
        """Internal synchronous transcription."""
        recognizer = self._create_recognizer(request.sample_rate)

        # Get audio data
        if request.audio_path:
            with open(request.audio_path, 'rb') as f:
                audio_data = f.read()
        else:
            audio_data = request.audio_data

        if not audio_data:
            return STTResponse(text='', language=request.language)

        # Handle different formats
        if request.format == 'wav':
            # Parse WAV file to get raw PCM
            audio_data = self._extract_pcm_from_wav(audio_data)
        elif request.format not in ['raw', 'pcm']:
            raise ValueError(f"Unsupported audio format: {request.format}")

        # Process audio in chunks
        chunk_size = 4000
        segments = []
        full_text = []

        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if recognizer.AcceptWaveform(chunk):
                result = json.loads(recognizer.Result())
                text = result.get('text', '')
                if text:
                    full_text.append(text)
                    if request.enable_timestamps and 'result' in result:
                        for word_info in result['result']:
                            segments.append(TranscriptSegment(
                                text=word_info['word'],
                                start_time=word_info.get('start', 0),
                                end_time=word_info.get('end', 0),
                                confidence=word_info.get('conf', 1.0)
                            ))

        # Get final result
        final_result = json.loads(recognizer.FinalResult())
        final_text = final_result.get('text', '')
        if final_text:
            full_text.append(final_text)

        text = ' '.join(full_text)
        text = self.clean_transcript(text)

        return STTResponse(
            text=text,
            segments=segments,
            language=request.language,
            confidence=1.0
        )

    def _extract_pcm_from_wav(self, wav_data: bytes) -> bytes:
        """Extract raw PCM data from WAV file."""
        wav_io = io.BytesIO(wav_data)
        with wave.open(wav_io, 'rb') as wav:
            return wav.readframes(wav.getnframes())

    def transcribe(self, request: STTRequest) -> STTResponse:
        """Transcribe audio synchronously."""
        return self._transcribe_sync(request)

    async def transcribe_async(self, request: STTRequest) -> STTResponse:
        """Transcribe audio asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(self._transcribe_sync, request)
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
        language: str = 'en',
        callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[TranscriptSegment]:
        """
        Transcribe audio stream in real-time.

        Yields TranscriptSegment for each complete utterance detected.
        """
        recognizer = self._create_recognizer(sample_rate)

        async for chunk in audio_stream:
            # Run recognition in executor to avoid blocking
            loop = asyncio.get_event_loop()

            def process_chunk(data):
                if recognizer.AcceptWaveform(data):
                    return json.loads(recognizer.Result())
                return None

            result = await loop.run_in_executor(
                self._executor,
                process_chunk,
                chunk
            )

            if result:
                text = result.get('text', '')
                if text:
                    text = self.clean_transcript(text)
                    if callback:
                        callback(text)

                    # Extract timing info if available
                    if 'result' in result:
                        words = result['result']
                        start_time = words[0].get('start', 0) if words else 0
                        end_time = words[-1].get('end', 0) if words else 0
                    else:
                        start_time = end_time = 0

                    yield TranscriptSegment(
                        text=text,
                        start_time=start_time,
                        end_time=end_time
                    )

        # Get final result
        final_result = json.loads(recognizer.FinalResult())
        final_text = final_result.get('text', '')
        if final_text:
            final_text = self.clean_transcript(final_text)
            if callback:
                callback(final_text)
            yield TranscriptSegment(text=final_text)

    def list_languages(self) -> List[str]:
        """List supported language codes."""
        return list(self.LANGUAGE_MODELS.keys())

    def health_check(self) -> bool:
        """Check if Vosk is available."""
        try:
            # Check if model path exists
            if not os.path.exists(self.model_path):
                return False

            # Try to import vosk
            from vosk import Model
            return True
        except Exception:
            return False

    def clean_transcript(self, text: str) -> str:
        """Clean Vosk transcription output."""
        import re

        text = text.strip()

        # Vosk sometimes adds "the" at the beginning incorrectly
        if text.startswith("the "):
            text = text[4:]

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text

    def preload_model(self):
        """Preload the model for faster first inference."""
        self._ensure_model_loaded()


class VoskLiveTranscriber:
    """
    Helper class for live microphone transcription.

    Usage:
        transcriber = VoskLiveTranscriber(provider)
        transcriber.start(callback=lambda text: print(text))
        # ... later ...
        transcriber.stop()
    """

    def __init__(self, provider: VoskProvider):
        self.provider = provider
        self._running = False
        self._paused = False
        self._thread = None
        self._callback = None
        self._stream = None
        self._pyaudio = None

    def start(self, callback: Callable[[str], None]):
        """Start live transcription with callback for recognized text."""
        if self._running:
            return

        try:
            import pyaudio
        except ImportError:
            raise ImportError(
                "pyaudio not installed. Install with: pip install pyaudio"
            )

        self._callback = callback
        self._running = True
        self._paused = False

        self._pyaudio = pyaudio.PyAudio()
        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.provider.sample_rate,
            input=True,
            frames_per_buffer=8192
        )

        import threading
        self._thread = threading.Thread(target=self._transcribe_loop)
        self._thread.start()

    def _transcribe_loop(self):
        """Main transcription loop."""
        recognizer = self.provider._create_recognizer()

        while self._running:
            if self._paused:
                import time
                time.sleep(0.1)
                continue

            try:
                data = self._stream.read(4096, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '')
                    if text and self._callback:
                        text = self.provider.clean_transcript(text)
                        if text:
                            self._callback(text)
            except Exception as e:
                print(f"Transcription error: {e}")

    def pause(self):
        """Pause transcription."""
        self._paused = True

    def resume(self):
        """Resume transcription."""
        self._paused = False

    def stop(self):
        """Stop transcription and cleanup."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()

        if self._pyaudio:
            self._pyaudio.terminate()
