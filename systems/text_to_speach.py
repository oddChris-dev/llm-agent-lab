import os
import re
import threading
import queue
import tempfile
import wave

import pyaudio
import soundfile as sf

import pyttsx3

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

from systems.system_base import SystemBase
from utils.text_tools import TextTools


class TextToSpeach(SystemBase):
    def __init__(self,
                 app,
                 tmp_path: str = "tmp",
                 default_voice: str = "en_sample",
                 model_path: str = "models/XTTS-v2",
                 cuda_lock: threading.Lock = threading.Lock()):
        super().__init__(app)

        temp_dir = tmp_path
        tempfile.tempdir = temp_dir

        self.tmp_path = tmp_path
        self.model_path = model_path
        self.ready_gate = threading.Event()
        self.cuda_lock = cuda_lock

        # thread for playing audio
        self.audio_queue = queue.Queue()
        self.audio_thread = threading.Thread(target=self.do_audio)

        # thread for generating audio samples with tts model
        self.speak_thread = threading.Thread(target=self.do_speak)
        self.speak_queue = queue.Queue()

        self.playing = False
        self.running = False
        self.model_loaded = False
        self.audio_count = 0
        self.max_split_length = 80
        self.clearing = False
        self.clear_lock = threading.Lock()

        # use pytts as a fallback
        self.pytts = pyttsx3.init()
        self.pytts_voices = self.pytts.getProperty('voices')
        self.pytts.setProperty('voice', self.pytts_voices[1].id)

        self.pyaudio = pyaudio.PyAudio()
        # text to speach model
        self.default_voice = default_voice
        self.tts_model = None
        self.speaker_embedding = None
        self.gpt_cond_latent = None
        self.idle_func = None

        self.voice_cache = {}

    def set_voice(self, voice_sample: str = "en_sample"):
        print(f"setting default voice to {voice_sample}")
        self.default_voice = voice_sample

    def load_model(self):
        config = XttsConfig()
        config.load_json(f"{self.model_path}/config.json")

        self.tts_model = Xtts.init_from_config(config)
        self.tts_model.load_checkpoint(config, checkpoint_dir=self.model_path, eval=True)
        self.tts_model.cuda()
        self.set_voice(self.default_voice)

    def clean_speach(self, text):
        text = re.sub(r'[^a-zA-Z0-9 \'%;:,.-=]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r' ,', ',', text)
        text = re.sub(r',$', '', text)
        text = TextTools.separate_acronyms(text)
        return text

    def generate_speech(self, prompt: str, output_file: str = "tmp/tts_output.wav"):
        prompt = self.clean_speach(prompt)
        print(f">{prompt}")

        try:
            # generate audio with the text to speach model
            outputs = self.tts_model.inference(
                prompt,
                "en",
                self.gpt_cond_latent,
                self.speaker_embedding
            )

            # write audio to temporary file
            sf.write(output_file, outputs["wav"], self.tts_model.config.audio.output_sample_rate)
        except Exception as ex:
            print(f"generate_speech {prompt} exception {ex}")

    def load_voice_file(self, voice_name):
        """Load a voice file from disk or database and cache latents and embeddings."""
        # Check if voice is already cached
        if voice_name in self.voice_cache:
            return self.voice_cache[voice_name]

        voice_path = f"{self.tmp_path}/{voice_name}.wav"

        print(f"Voice file '{voice_path}' not found on in cache. Loading from database.")

        # Check if the file exists on disk
        if not os.path.exists(voice_path):
            # Load from the database
            voice_model = self.get_voice(voice_name)
            if voice_model:
                voice_data = voice_model.get_data()
                if voice_data:
                    with open(voice_path, 'wb') as f:
                        f.write(voice_data)  # Save to disk
            else:
                raise FileNotFoundError(f"Voice '{voice_name}' not found in the database or file system.")

        # Now, load the conditioning latents and speaker embeddings
        gpt_cond_latent, speaker_embedding = self.tts_model.get_conditioning_latents(audio_path=voice_path)

        # Cache the loaded latents and embeddings
        self.voice_cache[voice_name] = (gpt_cond_latent, speaker_embedding)

        # remove temp file
        os.remove(voice_path)

        return gpt_cond_latent, speaker_embedding

    def do_speak_parts(self, voice_name, speach_parts, callback):
        self.app.media_player().fade_out()

        self.gpt_cond_latent, self.speaker_embedding = self.load_voice_file(voice_name)

        # generate audio for each of the parts of speech and queue for playback
        with self.clear_lock:
            with self.cuda_lock:
                for i, part in enumerate(speach_parts):
                    if not self.clearing:
                        self.audio_count += 1
                        output_file = f"{self.tmp_path}/speak_audio_{self.audio_count}.wav"
                        try:
                            self.generate_speech(prompt=part, output_file=output_file)
                            self.audio_queue.put({"file": output_file})
                        except Exception as ex:
                            print(f"do_speak_parts exception {ex}")
                            self.pytts.say(part)
                            self.pytts.runAndWait()

        self.audio_queue.put({"callback": callback})

    def play_audio(self, file_path: str = 'tmp/tts_output.wav'):
        # avoid feedback by pausing the microphone
        self.app.listener().pause()
        self.app.media_player().fade_out()

        self.playing = True
        try:
            wav = wave.open(file_path, 'rb')

            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(wav.getsampwidth()),
                channels=wav.getnchannels(),
                rate=wav.getframerate(),
                output=True
            )

            try:
                chunk_size = 4096
                data = wav.readframes(chunk_size)
                while data:
                    stream.write(data)
                    data = wav.readframes(chunk_size)
            except Exception as ex:
                print(f"play_audio exception {ex}")
            finally:
                stream.close()

        finally:
            self.playing = False

        self.app.listener().unpause()

    def check_idle(self):
        if self.is_idle() and self.idle_func:
            self.idle_func()

    def do_audio(self):
        while self.running:
            try:
                # Block until an audio file is available
                audio = self.audio_queue.get()
                if audio:
                    if "file" in audio:
                        if not self.clearing:
                            self.play_audio(audio["file"])
                        os.remove(audio["file"])

                    if "callback" in audio and audio["callback"]:
                        audio["callback"]()

                    if self.is_idle():
                        threading.Timer(2, self.check_idle).start()

            except Exception as ex:
                print(f"do_audio exception {ex}")
            finally:
                self.audio_queue.task_done()

    def is_idle(self):
        return not self.playing and self.audio_queue.qsize() == 0 and self.speak_queue.qsize() == 0

    def clear_audio(self):
        self.clearing = True
        with self.clear_lock:
            while self.audio_queue.qsize() > 0:
                audio = self.audio_queue.get(False)
                if audio:
                    if "file" in audio:
                        print("remove " + audio["file"])
                        os.remove(audio["file"])
                    if "callback" in audio:
                        audio["callback"]()
            self.clearing = False

    def wait_for_ready(self):
        self.ready_gate.wait()

    def do_speak(self):
        self.load_model()
        self.model_loaded = True
        self.ready_gate.set()

        while self.running:
            try:
                # Block until an audio file is available
                speach = self.speak_queue.get()
                if speach:
                    # split the prompt into smaller parts
                    prompt_parts = TextTools.split_speech(speach["text"], max_length=self.max_split_length)
                    self.do_speak_parts(speach["voice"], prompt_parts, speach["callback"])
            except Exception as ex:
                print(f"Exception: {ex}")
            finally:
                self.speak_queue.task_done()

    def say(self, speach_text):
        self.start()
        self.speak_queue.put({"voice": self.default_voice, "text": speach_text, "callback": None})

    def voice_say(self, voice_name, speach_text):
        self.start()
        self.speak_queue.put({"voice": voice_name, "text": speach_text, "callback": None})

    def voice_say_with_callback(self, voice_name, speach_text, callback):
        self.start()
        self.speak_queue.put({"voice": voice_name, "text": speach_text, "callback": callback})

    def clear(self):
        print("clear speech")
        self.speak_queue.queue.clear()
        self.clear_audio()

    def stop(self):
        if self.running:
            self.running = False
            self.clear_audio()
            self.audio_queue.put(None)
            self.speak_queue.put(None)
            self.audio_thread.join()
            self.speak_thread.join()

    def start(self):
        if not self.running:
            self.running = True

            # Start threads for processing speach and playing audio parts
            self.audio_thread.start()
            self.speak_thread.start()

            self.idle_func = self.app.media_player().fade_in
