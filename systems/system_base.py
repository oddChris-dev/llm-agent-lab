from models.agent_model import AgentModel
from models.game_model import GameModel
from models.page_model import PageModel
from models.session_model import SessionModel
from models.session_history_model import SessionHistoryModel
from models.session_player_model import SessionPlayerModel
from models.session_setting_model import SessionSettingModel
from models.session_transcript_model import SessionTranscriptModel
from models.voice_model import VoiceModel


class SystemBase:
    user_browser_string = "about:privatebrowsing"

    def __init__(self, app):
        self.app = app

    def get_agents(self):
        return AgentModel.get_all(self.app.db())

    def get_agent(self, agent_name):
        return AgentModel.get(self.app.db(), agent_name)

    def get_games(self):
        return GameModel.get_all(self.app.db())

    def get_game(self, game_name):
        return GameModel.get(self.app.db(), game_name)

    def get_voices(self):
        return VoiceModel.get_all(self.app.db())

    def get_voice(self, name):
        return VoiceModel(self.app.db(), name)

    def get_sessions(self):
        return SessionModel.get_all(self.app.db())

    def get_session(self, session_id):
        return SessionModel.get(self.app.db(), session_id)

    def get_session_players(self, session_id):
        return SessionPlayerModel.get_by_session_id(self.app.db(), session_id)

    def get_session_player(self, session_id, turn_number):
        return SessionPlayerModel.get(self.app.db(), session_id, turn_number)

    def get_session_settings(self, session_id):
        return SessionSettingModel.get_by_session_id(self.app.db(), session_id)

    def get_session_settings_limited(self, session_id, max_settings):
        settings = {}

        setting_count = 0
        for entry in self.get_session_settings(session_id):
            setting_count += 1
            if setting_count < max_settings:
                settings[entry.name] = entry.value

        if setting_count >= max_settings:
            print(f"warning: session {session_id} has more that settings than max: {setting_count} > {max_settings}")
        return settings

    def get_session_setting(self, session_id, setting_name):
        return SessionSettingModel.get(self.app.db(), session_id, setting_name)

    def get_session_transcripts(self, session_id):
        return SessionTranscriptModel.get_by_session_id(self.app.db(), session_id)

    def get_transcripts(self):
        return SessionTranscriptModel.get_all(self.app.db())

    def get_session_transcript(self, transcript_id):
        return SessionTranscriptModel.get(self.app.db(), transcript_id)

    def add_session_transcript(self, session_id, url, agent, content):
        transcript = SessionTranscriptModel(
            self.app.db(),
            id=None,
            session_id=session_id,
            url=url,
            agent=agent,
            content=content)
        transcript.save()

    def get_session_transcripts_since(self, session_id, timestamp):
        return SessionTranscriptModel.get_new_session_transcripts_since(
            self.app.db(),
            session_id,
            timestamp
        )

    def get_transcripts_since(self, timestamp):
        return SessionTranscriptModel.get_new_transcripts_since(
            self.app.db(),
            timestamp
        )

    def get_session_history(self, session_id):
        return SessionHistoryModel.get_by_session_id(self.app.db(), session_id)

    def get_session_history_by_id(self, history_id):
        return SessionHistoryModel.get(self.app.db(), history_id)

    def add_session_history(self, session_id, role, content):
        history = SessionHistoryModel(self.app.db(),
                                      id=None,
                                      session_id=session_id,
                                      role=role,
                                      content=content)
        history.save()
        return history

    def get_history(self, history_id):
        return SessionHistoryModel.get(self.app.db(), history_id)

    def get_agents_from_history(self, session_id, max_results):
        agents = []
        agent_history = SessionHistoryModel.get_latest_by_role(
            self.app.db(),
            session_id,
            "agent-*",
            max_results,
            use_wildcard=True
        )

        for entry in agent_history:
            agents.append({"role": "tool", "tool": entry.role, "content": entry.content})

        return agents

    def get_user_from_history(self, session_id, max_results):
        users = []

        user_history = SessionHistoryModel.get_latest_by_role(
            self.app.db(),
            session_id,
            "user",
            max_results
        )

        for entry in user_history:
            users.append({"role": "user", "content": entry.content})

        return users

    def get_pages(self, session_id, max_results):
        return PageModel.get_summarized(self.app.db(), session_id, 1, max_results)

    def get_unloaded_pages(self, session_id, max_results):
        return PageModel.get_unloaded_pages(self.app.db(), session_id, max_results)

    def get_last_page(self, session_id):
        return PageModel.get_summarized(self.app.db(), session_id, 1, 1)

    def get_session_page(self, session_id, url):
        return PageModel.get_by_url(self.app.db(), url, session_id)

    def get_search_results(self, session_id, search_term, max_results):
        return PageModel.get_by_search_term(self.app.db(), session_id, search_term, max_results)

    def get_search_pages(self, session_id, max_results):
        return PageModel.get_search_results(self.app.db(), session_id, max_results)

    def get_user_pages(self, session_id, max_pages):
        return PageModel.get_by_parent_url(
            self.app.db(),
            self.user_browser_string,
            session_id,
            max_pages
        )

    def get_discovered_pages(self, session_id, max_pages):
        return PageModel.get_by_not_parent_url(
            self.app.db(),
            self.user_browser_string,
            session_id,
            max_pages
        )
