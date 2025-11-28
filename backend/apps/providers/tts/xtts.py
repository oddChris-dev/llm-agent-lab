"""
XTTS-v2 TTS Provider.

Provides integration with Coqui XTTS-v2 for high-quality voice cloning
and text-to-speech synthesis.
"""

import os
import io
import re
import tempfile
import asyncio
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import torch
import soundfile as sf

from .base import (
    BaseTTSProvider,
    TTSRequest,
    TTSResponse,
    VoiceInfo,
)


class XTTSProvider(BaseTTSProvider):
    """
    XTTS-v2 provider for local voice cloning and TTS.

    Config options:
        model_path: Path to XTTS-v2 model directory
        voices_path: Path to voice sample files
        device: Device to use ('cuda', 'cpu', 'auto')
        use_deepspeed: Enable DeepSpeed optimization (default: False)
    """

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.model_path = self.config.get('model_path', 'models/XTTS-v2')
        self.voices_path = self.config.get('voices_path', 'voices')
        self.device = self.config.get('device', 'auto')
        self.use_deepspeed = self.config.get('use_deepspeed', False)

        self._model = None
        self._voice_cache: Dict[str, tuple] = {}
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return 'xtts'

    @property
    def supports_cloning(self) -> bool:
        return True

    @property
    def supports_streaming(self) -> bool:
        return True

    def _ensure_model_loaded(self):
        """Load model if not already loaded."""
        if self._model is not None:
            return

        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            from TTS.tts.models.xtts import Xtts
        except ImportError:
            raise ImportError(
                "TTS package not installed. Install with: pip install TTS"
            )

        config = XttsConfig()
        config.load_json(os.path.join(self.model_path, "config.json"))

        self._model = Xtts.init_from_config(config)
        self._model.load_checkpoint(
            config,
            checkpoint_dir=self.model_path,
            eval=True,
            use_deepspeed=self.use_deepspeed
        )

        # Determine device
        if self.device == 'auto':
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            device = self.device

        if device == 'cuda':
            self._model.cuda()

    def _get_voice_conditioning(self, voice_id: str) -> tuple:
        """Get or compute voice conditioning from cache."""
        if voice_id in self._voice_cache:
            return self._voice_cache[voice_id]

        # Try to find voice file
        voice_path = None
        for ext in ['.wav', '.mp3', '.ogg']:
            path = os.path.join(self.voices_path, f"{voice_id}{ext}")
            if os.path.exists(path):
                voice_path = path
                break

        if not voice_path:
            raise ValueError(f"Voice '{voice_id}' not found in {self.voices_path}")

        # Compute conditioning latents
        gpt_cond_latent, speaker_embedding = self._model.get_conditioning_latents(
            audio_path=voice_path
        )

        self._voice_cache[voice_id] = (gpt_cond_latent, speaker_embedding)
        return gpt_cond_latent, speaker_embedding

    def _get_voice_from_sample(self, sample: bytes) -> tuple:
        """Compute conditioning from audio sample bytes."""
        # Write sample to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(sample)
            temp_path = f.name

        try:
            gpt_cond_latent, speaker_embedding = self._model.get_conditioning_latents(
                audio_path=temp_path
            )
            return gpt_cond_latent, speaker_embedding
        finally:
            os.unlink(temp_path)

    def _synthesize_sync(self, request: TTSRequest) -> TTSResponse:
        """Internal synchronous synthesis."""
        self._ensure_model_loaded()

        # Get voice conditioning
        if request.voice_sample:
            gpt_cond_latent, speaker_embedding = self._get_voice_from_sample(
                request.voice_sample
            )
        else:
            gpt_cond_latent, speaker_embedding = self._get_voice_conditioning(
                request.voice_id
            )

        # Clean text
        text = self.clean_text(request.text)

        # Generate audio
        outputs = self._model.inference(
            text,
            request.language,
            gpt_cond_latent,
            speaker_embedding,
            speed=request.speed
        )

        # Convert to bytes
        audio_buffer = io.BytesIO()
        sample_rate = self._model.config.audio.output_sample_rate
        sf.write(audio_buffer, outputs["wav"], sample_rate, format='WAV')
        audio_data = audio_buffer.getvalue()

        # Calculate duration
        duration_ms = int(len(outputs["wav"]) / sample_rate * 1000)

        return TTSResponse(
            audio_data=audio_data,
            sample_rate=sample_rate,
            format='wav',
            duration_ms=duration_ms
        )

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech synchronously."""
        return self._synthesize_sync(request)

    async def synthesize_async(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech asynchronously."""
        loop = asyncio.get_event_loop()
        async with self._lock:
            return await loop.run_in_executor(
                self._executor,
                partial(self._synthesize_sync, request)
            )

    async def stream(self, request: TTSRequest) -> bytes:
        """
        Stream audio generation.

        XTTS supports streaming inference for real-time playback.
        """
        self._ensure_model_loaded()

        # Get voice conditioning
        if request.voice_sample:
            gpt_cond_latent, speaker_embedding = self._get_voice_from_sample(
                request.voice_sample
            )
        else:
            gpt_cond_latent, speaker_embedding = self._get_voice_conditioning(
                request.voice_id
            )

        text = self.clean_text(request.text)

        # Use streaming inference
        chunks = self._model.inference_stream(
            text,
            request.language,
            gpt_cond_latent,
            speaker_embedding,
            speed=request.speed
        )

        sample_rate = self._model.config.audio.output_sample_rate

        for chunk in chunks:
            # Convert numpy array to wav bytes
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, chunk.cpu().numpy(), sample_rate, format='WAV')
            yield audio_buffer.getvalue()

    def list_voices(self) -> List[VoiceInfo]:
        """List available voice samples."""
        voices = []

        if not os.path.exists(self.voices_path):
            return voices

        for filename in os.listdir(self.voices_path):
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.wav', '.mp3', '.ogg']:
                voices.append(VoiceInfo(
                    id=name,
                    name=name.replace('_', ' ').title(),
                    language='en',  # Default assumption
                    is_cloned=True
                ))

        return voices

    def clone_voice(
        self,
        name: str,
        audio_sample: bytes,
        description: Optional[str] = None
    ) -> VoiceInfo:
        """
        Create a cloned voice from an audio sample.

        Saves the audio sample as a voice file for future use.
        """
        self._ensure_model_loaded()

        # Ensure voices directory exists
        os.makedirs(self.voices_path, exist_ok=True)

        # Save voice file
        voice_path = os.path.join(self.voices_path, f"{name}.wav")
        with open(voice_path, 'wb') as f:
            f.write(audio_sample)

        # Pre-compute and cache conditioning
        gpt_cond_latent, speaker_embedding = self._model.get_conditioning_latents(
            audio_path=voice_path
        )
        self._voice_cache[name] = (gpt_cond_latent, speaker_embedding)

        return VoiceInfo(
            id=name,
            name=name.replace('_', ' ').title(),
            language='en',
            description=description,
            is_cloned=True
        )

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice."""
        # Remove from cache
        self._voice_cache.pop(voice_id, None)

        # Remove file
        for ext in ['.wav', '.mp3', '.ogg']:
            path = os.path.join(self.voices_path, f"{voice_id}{ext}")
            if os.path.exists(path):
                os.remove(path)
                return True

        return False

    def health_check(self) -> bool:
        """Check if XTTS is available."""
        try:
            # Check if model path exists
            config_path = os.path.join(self.model_path, "config.json")
            if not os.path.exists(config_path):
                return False

            # Try to import TTS
            from TTS.tts.configs.xtts_config import XttsConfig
            return True
        except Exception:
            return False

    def clean_text(self, text: str) -> str:
        """Clean text for XTTS synthesis."""
        # Remove unsupported characters but keep basic punctuation
        text = re.sub(r'[^a-zA-Z0-9 \'%;:,.\-=!?]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r' ,', ',', text)
        text = re.sub(r',$', '', text)

        # Separate acronyms (e.g., "NASA" -> "N A S A")
        text = re.sub(r'\b([A-Z]{2,})\b', lambda m: ' '.join(m.group(1)), text)

        return text.strip()

    def preload_model(self):
        """Preload the model for faster first inference."""
        self._ensure_model_loaded()

    def clear_cache(self):
        """Clear the voice conditioning cache."""
        self._voice_cache.clear()
