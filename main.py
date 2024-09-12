from flask_bootstrap import Bootstrap5
from flask import Flask
from flask_wtf import CSRFProtect

from pages.agent_page import AgentPage
from pages.game_page import GamePage
from pages.index_page import IndexPage
from pages.media_page import MediaPage
from pages.session_history_page import SessionHistoryPage
from pages.session_page import SessionPage
from pages.session_players_page import SessionPlayersPage
from pages.session_settings_page import SessionSettingsPage
from pages.session_transcripts_page import SessionTranscriptsPage
from pages.voice_page import VoicePage
from systems.app import App

app = App()

flask_app = Flask(__name__)
flask_app.config['SECRET_KEY'] = 'super secret key'
#flask_app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'slate'


flask_app.register_blueprint(IndexPage(app).blueprint)
flask_app.register_blueprint(MediaPage(app).blueprint)
flask_app.register_blueprint(VoicePage(app).blueprint)
flask_app.register_blueprint(AgentPage(app).blueprint)
flask_app.register_blueprint(GamePage(app).blueprint)
flask_app.register_blueprint(SessionPage(app).blueprint)
flask_app.register_blueprint(SessionTranscriptsPage(app).blueprint)
flask_app.register_blueprint(SessionPlayersPage(app).blueprint)
flask_app.register_blueprint(SessionSettingsPage(app).blueprint)
flask_app.register_blueprint(SessionHistoryPage(app).blueprint)

bootstrap = Bootstrap5(flask_app)
csrf = CSRFProtect(flask_app)


if __name__ == "__main__":
    try:
        flask_app.run(debug=True, use_reloader=False)
    finally:
        app.stop()
