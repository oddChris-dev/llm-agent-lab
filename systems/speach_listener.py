from vosk import Model, KaldiRecognizer
import pyaudio
import threading
import json
import time


class SpeachListener:
    def __init__(self, model_path: str = "models/vosk-model-en-us-0.22"):
        self.mic = None
        self.stream = None
        self.callback = None
        self.running = False
        self.paused = False
        self.pause_gate = threading.Lock()
        self.model_path = model_path
        self.listen_thread = threading.Thread(target=self.do_listen)
        self.model = None
        self.recognizer = None

    def open_mic(self):
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192
        )
        self.stream.start_stream()

    def close_mic(self):
        try:
            if self.stream:
                self.stream.stop_stream()
        except Exception as ex:
            print(f"exception closing mic {ex}")

    def do_listen(self):
        self.open_mic()
        print("listen system ready")

        while self.running:
            if not self.paused:
                try:
                    self.pause_gate.acquire()
                    self.do_listen_and_callback()
                except Exception as ex:
                    if not self.paused:
                        print(f"listening exception: {ex}")
                        # reset the mic
                        self.close_mic()
                        self.open_mic()

                finally:
                    self.pause_gate.release()
            else:
                time.sleep(1)

        self.close_mic()

    @staticmethod
    def clean_audio_string(result):
        text = json.loads(result)["text"]
        text = text[len("the"):] if text.startswith("the") else text
        return text

    def do_listen_and_callback(self):
        data = self.stream.read(4096)
        if self.recognizer.AcceptWaveform(data):
            text = self.clean_audio_string(self.recognizer.Result())
            if text:
                print(f"heard: {text}")
                if self.callback:
                    self.callback(text)

    def pause(self):
        if self.running:
            self.paused = True
            self.close_mic()
            self.pause_gate.acquire()

    def unpause(self):
        if self.running:
            self.open_mic()
            self.pause_gate.release()
            self.paused = False

    def stop(self):
        if self.running:
            self.running = False
            self.listen_thread.join()

    def start(self, callback):
        if not self.running:
            if not self.model:
                self.model = Model(self.model_path)
                self.recognizer = KaldiRecognizer(self.model, 16000)
            self.running = True
            self.callback = callback
            self.listen_thread.start()
