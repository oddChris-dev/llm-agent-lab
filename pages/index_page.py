from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField, TextAreaField

from pages.base_page import BasePage

class IndexPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('index_page', __name__, template_folder='templates')
        self.routes()

    class StartTranscriptsButtonForm(FlaskForm):
        start_button = SubmitField('Play Any', render_kw={'class': 'btn btn-info btn-sm'})

    class SkipTranscriptButtonForm(FlaskForm):
        skip_button = SubmitField('Skip Current', render_kw={'class': 'btn btn-info btn-sm'})

    class ClearTranscriptButtonForm(FlaskForm):
        clear_button = SubmitField('Clear All', render_kw={'class': 'btn btn-info btn-sm'})

    class StopTranscriptsButtonForm(FlaskForm):
        stop_button = SubmitField('Stop', render_kw={'class': 'btn btn-info btn-sm'})

    class StartBrowserButtonForm(FlaskForm):
        start_browser_button = SubmitField('Start User Browser', render_kw={'class': 'btn btn-info btn-sm'})

    class StartListenerButtonForm(FlaskForm):
        start_listener_button = SubmitField('Start Voice Listener', render_kw={'class': 'btn btn-info btn-sm'})

    class SessionButtonForm(FlaskForm):
        session_button = SubmitField('Edit Sessions', render_kw={'class': 'btn btn-info btn-sm'})

    class UserInputForm(FlaskForm):
        input_text = TextAreaField('Send Text to Session', render_kw={"rows": 7})
        submit = SubmitField('Submit', render_kw={'class': 'btn btn-info btn-sm'})

    def routes(self):
        # Flask pages for interacting with the AI system
        @self.blueprint.route('/')
        def index():
            return render_template(
                'index.html',
                game_system=self.app.game(),
                transcript_player=self.app.transcripts(),
                music_player=self.app.media_player(),
                sessions=self.get_sessions(),
                music_start_form=self.StartMusicButtonForm(),
                music_next_form=self.NextSongButtonForm(),
                music_prev_form=self.PreviousSongButtonForm(),
                music_stop_form=self.StopMusicButtonForm(),
                start_transcripts_form=self.StartTranscriptsButtonForm(),
                skip_transcript_form=self.SkipTranscriptButtonForm(),
                clear_transcripts_form=self.ClearTranscriptButtonForm(),
                stop_transcript_form=self.StopTranscriptsButtonForm(),
                start_session_form=self.StartButtonForm(),
                stop_session_form=self.StopButtonForm(),
                browser_form=self.StartBrowserButtonForm(),
                listener_form=self.StartListenerButtonForm(),
                session_form=self.SessionButtonForm(),
                input_form=self.UserInputForm()
            )

        @self.blueprint.route('/user_input', methods=['POST'])
        def user_input():
            self.app.game().on_user_input(
                request.form['input_text']
            )

            return redirect(url_for('index_page.index'))

        @self.blueprint.route('/listener/start', methods=['GET', 'POST'])
        def start_listener():
            self.app.game().start_voice_listener()
            return redirect(url_for('index_page.index'))

        @self.blueprint.route('/browser/start', methods=['GET', 'POST'])
        def start_browser():
            self.app.game().start_user_browser()
            return redirect(url_for('index_page.index'))

        # Route to stop AI, browser, and speech
        @self.blueprint.route('/stop', methods=['POST'])
        def stop_all():
            self.app.game().stop()
            return redirect(url_for('index_page.index'))

        # Route to quit the application
        @self.blueprint.route('/quit', methods=['POST'])
        def quit_app():
            # Stopping the systems gracefully
            self.app.stop()
            exit()  # This will terminate the server process
