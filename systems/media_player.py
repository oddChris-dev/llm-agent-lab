import os
import threading
import time
import random

class MediaPlayer:
    def __init__(self, media_path, vlc_player_path=None):
        if vlc_player_path:
            os.environ['PATH'] += os.pathsep + vlc_player_path
            os.add_dll_directory(vlc_player_path)

        self.media_path = media_path

        self.fade_interval = 0.1  # Interval between volume changes (seconds)
        self.fade_duration = 3
        self.play_volume = 60
        self.quiet_volume = 20

        self.vlc_instance = None  # music player
        self.media_list_player = None # control the playlist
        self.media_player = None # control the volume

        self.media_list = None
        self.fade_thread = None  # Track the current fade thread
        self.playing = False
        self.faded = True
        self.fading = False

    def load_media_list(self, vlc_instance, media_list_player, folder_path):
        media_list = []
        """Load all media files from the specified folder."""
        if not os.path.isdir(folder_path):
            raise ValueError(f"Invalid folder path: {folder_path}")

        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith(('.mp3', '.mp4', '.mkv', '.avi', '.mov', '.mpg')):
                media_path = os.path.join(folder_path, file_name)
                media_list.append(self.vlc_instance.media_new(media_path))

        print(f"loaded and shuffled {len(media_list)} songs")
        random.shuffle(media_list)

        vlc_media_list = vlc_instance.media_list_new()

        for media in media_list:
            vlc_media_list.add_media(media)

        media_list_player.set_media_list(vlc_media_list)

    def set_volume(self, volume):
        """Set the media player's volume."""
        # print(f"setting volume to {volume}")
        self.media_player.audio_set_volume(volume)

    def start(self):
        if not self.playing:
            print("start media player")
            if not self.vlc_instance:
                import vlc

                self.vlc_instance = vlc.Instance()  # Initialize without extra parameters

                self.media_player = vlc.MediaPlayer(self.vlc_instance)
                self.media_player.audio_set_volume(0)

                self.media_list_player = vlc.MediaListPlayer(self.vlc_instance)
                self.media_list_player.set_playback_mode(vlc.PlaybackMode.loop)

                self.load_media_list(self.vlc_instance, self.media_list_player, self.media_path)

                self.media_list_player.play()
                self.media_list_player.pause()

            self.set_volume(self.quiet_volume)
            self.playing = True
            self.faded = True
            self.fading = False

            self.media_list_player.pause()

            self.fade_in()

    def stop(self):
        if self.playing:
            print("stop media player")

            self.fade_out()
            self.media_list_player.pause()
            self.playing = False

    def fade_in(self):
        if not self.playing:
            return

        if not self.faded or self.media_player.audio_get_volume() == self.play_volume:
            return

        print("fade in media player")

        self.faded = False
        self.fading = False

        """Fade in volume from 0 to 100% over the specified duration."""

        def fade_in_thread():
            start_time = time.time()
            end_time = start_time + self.fade_duration
            initial_volume = self.media_player.audio_get_volume()
            volume = initial_volume
            target_volume = self.play_volume

            while time.time() < end_time and volume < target_volume and self.playing:
                elapsed_time = time.time() - start_time
                progress = min(elapsed_time / self.fade_duration, 1)  # Normalize progress to 1
                volume = int(initial_volume + progress * (target_volume - initial_volume))
                self.set_volume(volume)
                time.sleep(self.fade_interval)

            if not self.fading:
                self.set_volume(target_volume)

        # Start the fade-in effect in a new thread

        self.fade_thread = threading.Thread(target=fade_in_thread)
        self.fade_thread.start()

    def fade_out(self):
        if not self.playing:
            return

        if self.fading or self.media_player.audio_get_volume() == self.quiet_volume:
            return

        print("fade out media player")

        self.fading = True
        self.faded = True

        def fade_out_thread():
            start_time = time.time()
            end_time = start_time + self.fade_duration
            initial_volume = self.media_player.audio_get_volume()
            volume = initial_volume
            target_volume = self.quiet_volume

            while time.time() < end_time and volume > target_volume and self.fading:
                elapsed_time = time.time() - start_time
                progress = min(elapsed_time / self.fade_duration, 1)  # Normalize progress to 1
                volume = int(initial_volume - progress * (initial_volume - target_volume))
                self.set_volume(volume)
                time.sleep(self.fade_interval)

            if self.fading:
                self.set_volume(target_volume)

            self.fading = False

        self.fade_thread = threading.Thread(target=fade_out_thread)
        self.fade_thread.start()

    def next_media(self):
        if not self.playing:
            self.start()

        print("next media")
        self.media_list_player.next()

    def previous_media(self):
        if not self.playing:
            self.start()

        print("previous media")
        self.media_list_player.previous()
