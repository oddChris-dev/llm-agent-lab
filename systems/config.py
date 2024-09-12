import json


class Config:
    def __init__(self, config_file: str = "config.json"):
        with open(config_file, 'r') as file:
            config = json.load(file)

            # Load paths and other configurations from JSON
            self.default_voice = config.get('default_voice', 'en_sample')
            self.playlist_path = config.get('playlist_path', 'stream_playlist/')
            self.slideshow_path = config.get('slideshow_path', 'stream_pics/')
            self.ai_model_path = config.get('ai_model_path',
                                            'models/Meta-Llama-3.1-8B-Instruct')
            self.speech_to_text_model_path = config.get('speech_to_text_model_path',
                                                        'models/vosk-model-en-us-0.22')
            self.text_to_speech_model_path = config.get('text_to_speech_model_path', 'models/XTTS-v2')
            self.audio_temp_path = config.get('audio_temp_path', 'stream_audio_tmp/')
            self.auto_play_media = config.get('auto_play_media', False)
            self.listen_for_input = config.get('listen_for_input', False)
            self.vlc_player_path = config.get('vlc_player_path', r'C:\Program Files\VideoLAN\VLC')

            # Load database configuration from JSON
            self.db_host = config['mysql']['host']
            self.db_port = config['mysql']['port']
            self.db_database = config['mysql']['database']
            self.db_user = config['mysql']['user']
            self.db_password = config['mysql']['password']

            # os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
