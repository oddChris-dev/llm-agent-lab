import queue
import re
import threading
import time

from systems.system_base import SystemBase
from utils.html_tools import HtmlTools


class TranscriptPlayer(SystemBase):
    def __init__(self, app, check_interval=15):
        super().__init__(app)

        self.running = False
        self.showing = True
        self.show_condition = threading.Condition()

        self.show_queue = queue.Queue()
        self.show_thread = None
        self.check_interval = check_interval  # Time interval to check for new transcripts
        self.last_checked_timestamp = None  # Timestamp to track the last checked time
        self.check_thread = None
        self.session_id = None

    def clear(self):
        self.last_checked_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.show_queue.queue.clear()
        self.app.speech().clear()
        self.end_show()

    def show(self, url):
        self.app.instance.browser().show(url)

    def say(self, voice, text):
        self.app.instance.speech().voice_say_with_callback(voice, text, self.done_speaking)
        self.app.instance.speech().start()

    def done_speaking(self):
        print("done speaking")
        self.end_show()

    def wait_on_show(self):
        with self.show_condition:
            while self.showing:
                self.show_condition.wait()

    def start_show(self):
        with self.show_condition:
            if not self.showing:
                self.showing = True  # Indicate the start of a show

    def end_show(self):
        with self.show_condition:
            if self.showing:
                self.showing = False
                self.show_condition.notify_all()  # Notify all waiting threads to proceed

    def show_and_say(self, url, voice, text):
        self.show_queue.put({"url": url, "voice": voice, "text": text})
        print(f"show_and_say - show queue size {self.show_queue.qsize()}")
        if not self.running:
            self.start()

    def do_show(self):
        while self.running:
            next_show = self.show_queue.get()
            try:
                print(f"do_show {next_show} - show queue {self.show_queue}")
                if next_show and self.running:
                    self.start_show()
                    self.say(next_show["voice"], next_show["text"])
                    self.show(next_show["url"])
                    self.wait_on_show()
            except Exception as ex:
                print(f"do_show exception {ex}")

    def stop(self):
        if self.running:
            self.running = False
            self.show_queue.put(None)
            self.end_show()
            self.session_id = None
            if self.show_thread:
                self.show_thread.join()
            if self.check_thread:
                self.check_thread.join()

    def start(self):
        if not self.running:
            self.running = True
            self.show_thread = threading.Thread(target=self.do_show)
            self.show_thread.start()
            self.check_thread = threading.Thread(target=self.check_for_new_transcripts)
            self.check_thread.start()

    def check_for_new_transcripts(self):
        while self.running:
            try:
                if self.show_queue.qsize() == 0:
                    new_transcripts = self.query_new_transcripts()
                    for transcript in new_transcripts:
                        # Assuming 'voice' and 'text' are derived from transcript data
                        agent = self.get_agent(transcript.agent)
                        text = re.sub(HtmlTools.url_pattern, '', transcript.content, flags=re.IGNORECASE).strip()
                        text = re.sub(r'\*\s*[^*]+\s*\*', '', text)
                        self.show_and_say(transcript.url, agent.voice, text)
            except Exception as ex:
                print(f"check_for_new_transcripts exception: {ex}")
            time.sleep(self.check_interval)

    def query_new_transcripts(self):
        """Query new transcripts since the last check timestamp."""
        if self.last_checked_timestamp is None:
            # Initialize to the current time if no previous timestamp is set
            self.last_checked_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        print(self.last_checked_timestamp)

        if self.session_id:
            new_transcripts = self.get_session_transcripts_since(self.session_id, self.last_checked_timestamp)
        else:
            new_transcripts = self.get_transcripts_since(self.last_checked_timestamp)

        # Update the timestamp to the latest transcript time if available
        if new_transcripts and len(new_transcripts) > 0:
            self.last_checked_timestamp = new_transcripts[-1].timestamp

        return new_transcripts
