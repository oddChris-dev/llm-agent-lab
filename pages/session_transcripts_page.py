from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField

from pages.base_page import BasePage


class SessionTranscriptsPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('session_transcripts_page', __name__, template_folder='pages/templates')
        self.routes()

    class PlayTranscriptsButtonForm(FlaskForm):
        play_button = SubmitField('Play', render_kw={'class': 'btn btn-info btn-sm'})

    def routes(self):
        @self.blueprint.route('/transcripts', methods=['GET'])
        def transcripts():
            return render_template(
                'session/session_transcripts.html',
                sessions=self.get_sessions(),
                transcripts=self.get_transcripts(),
                play_form=self.PlayTranscriptsButtonForm(),
                delete_form=self.DeleteButtonForm(),
                done_form=self.DoneButtonForm()
            )

        @self.blueprint.route('/session/<session_id>/transcripts', methods=['GET'])
        def session_transcripts(session_id):
            return render_template(
                'session/session_transcripts.html',
                session=self.get_session(session_id),
                transcripts=self.get_session_transcripts(session_id),
                play_form=self.PlayTranscriptsButtonForm(),
                delete_form=self.DeleteButtonForm(),
                done_form=self.DoneButtonForm()
            )

        @self.blueprint.route('/transcripts/start', methods=['GET', 'POST'])
        def start_transcripts():
            self.app.transcripts().start()
            return redirect(request.referrer or url_for('index_page.index'))

        @self.blueprint.route('/transcripts/play/<transcript_id>', methods=['GET', 'POST'])
        def play_transcript(transcript_id):
            transcript = self.get_session_transcript(transcript_id)

            if transcript:
                self.app.transcripts().session_id = transcript.session_id
                self.app.transcripts().last_checked_timestamp = transcript.timestamp

                agent = self.get_agent(transcript.agent)
                if agent:
                    self.app.transcripts().show_and_say(transcript.url, agent.voice, transcript.content)

            return redirect(request.referrer or url_for('index_page.index'))

        @self.blueprint.route('/transcripts/stop', methods=['GET', 'POST'])
        def stop_transcripts():
            self.app.transcripts().stop()
            self.app.speech().clear()
            self.app.transcripts().session_id = None
            return redirect(request.referrer or url_for('index_page.index'))

        @self.blueprint.route('/transcripts/skip', methods=['GET', 'POST'])
        def skip_transcript():
            self.app.speech().clear()
            return redirect(request.referrer or url_for('index_page.index'))

        @self.blueprint.route('/transcripts/clear', methods=['GET', 'POST'])
        def clear_transcripts():
            self.app.transcripts().clear()
            self.app.speech().clear()
            return redirect(request.referrer or url_for('index_page.index'))

        @self.blueprint.route('/transcripts/play/<transcript_id>', methods=['GET', 'POST'])
        def play_session_transcript(session_id, transcript_id):
            transcript = self.get_session_transcript(transcript_id)

            if transcript:
                self.app.transcripts().session_id = transcript.session_id
                self.app.transcripts().last_checked_timestamp = transcript.timestamp

                agent = self.get_agent(transcript.agent)
                if agent:
                    self.app.transcripts().show_and_say(transcript.url, agent.voice, transcript.content)

            return redirect(request.referrer or url_for('session_transcripts_page.session_transcripts', session_id=session_id))

        @self.blueprint.route('/session/<session_id>/transcript/delete/<transcript_id>', methods=['GET', 'POST'])
        def delete_transcript(session_id, transcript_id):
            transcript = self.get_session_transcript(transcript_id)

            if transcript:
                transcript.delete()

            # Render the list of transcripts
            return redirect(url_for('session_transcripts_page.session_transcripts', session_id=session_id))

        @self.blueprint.route('/session/<session_id>/transcripts/start', methods=['GET', 'POST'])
        def start_session_transcripts(session_id):
            self.app.transcripts().session_id = session_id
            self.app.transcripts().start()
            return redirect(request.referrer or url_for('session_page.view_session', session_id=session_id))

