from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired

from models.session_model import SessionModel
from pages.base_page import BasePage
from systems.game_moves import GameMoves


class SessionPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('session_page', __name__, template_folder='pages/templates')
        self.routes()

    class SessionForm(FlaskForm):
        name = StringField('Name', validators=[DataRequired()])
        game = SelectField('Game', validators=[DataRequired()])
        judge = SelectField('Transcript Judge', validators=[DataRequired()])
        summary = SelectField('Page Summarizer', validators=[DataRequired()])
        submit = SubmitField('Save')

        def set_agents(self, agents):
            agent_choices = [(agent.name, agent.name) for agent in agents]
            self.judge.choices = agent_choices
            self.summary.choices = agent_choices

        def set_games(self, games):
            self.game.choices = [(game.name, game.name) for game in games]

        def set_session(self, session):
            self.name.data = session.name
            self.game.data = session.game
            self.judge.data = session.judge
            self.summary.data = session.summary

    class DetailsButtonForm(FlaskForm):
        details_button = SubmitField('Details', render_kw={'class': 'btn btn-info btn-sm'})

    class PlayersButtonForm(FlaskForm):
        players_button = SubmitField('Players', render_kw={'class': 'btn btn-info btn-sm'})

    class SettingsButtonForm(FlaskForm):
        settings_button = SubmitField('Settings', render_kw={'class': 'btn btn-info btn-sm'})

    class HistoryButtonForm(FlaskForm):
        history_button = SubmitField('History', render_kw={'class': 'btn btn-info btn-sm'})

    class TranscriptButtonForm(FlaskForm):
        transcript_button = SubmitField('Transcript', render_kw={'class': 'btn btn-info btn-sm'})

    class PlayButtonForm(FlaskForm):
        play_button = SubmitField('Play Transcript', render_kw={'class': 'btn btn-success btn-sm'})


    def routes(self):
        @self.blueprint.route('/sessions', methods=['GET'])
        def sessions():
            return render_template(
                'session/session_list.html',
                sessions=self.get_sessions(),
                start_form=self.StartButtonForm(),
                play_form=self.PlayButtonForm(),
                detail_form=self.DetailsButtonForm(),
                new_form=self.NewButtonForm(),
                delete_form=self.DeleteButtonForm(),
                player_form=self.PlayersButtonForm(),
                edit_form=self.EditButtonForm(),
                history_form=self.HistoryButtonForm(),
                transcript_form=self.TranscriptButtonForm(),
                settings_form=self.SettingsButtonForm()
            )

        @self.blueprint.route('/sessions/<session_id>', methods=['GET'])
        def view_session(session_id):
            session = self.get_session(session_id)
            game_moves = GameMoves(self.app, self.get_session(session_id))

            prompt_replacements = {
                "current_user_page": game_moves.prepare_prompt("%CURRENT_USER_PAGE%"),
                "current_page": game_moves.prepare_prompt("%CURRENT_PAGE%"),
                "searches": game_moves.prepare_prompt("%SEARCHES%"),
                "links": game_moves.prepare_prompt("%LINKS%"),
                "pages": game_moves.prepare_prompt("%PAGES%"),
                "settings": game_moves.prepare_prompt("%SETTINGS%"),
                "agents":game_moves.prepare_prompt("%AGENTS%")
            }

            return render_template(
                'session/session_view.html',
                session=session,
                prompt_replacements=prompt_replacements,
                players=self.get_session_players(session_id),
                settings=self.get_session_settings(session_id),
                start_form=self.StartButtonForm(),
                edit_form=self.EditButtonForm(),
                player_form=self.PlayersButtonForm(),
                history_form=self.HistoryButtonForm(),
                transcript_form=self.TranscriptButtonForm(),
                settings_form=self.SettingsButtonForm(),
                delete_form=self.DeleteButtonForm()
            )

        @self.blueprint.route('/sessions/new', methods=['GET', 'POST'])
        def new_session():
            games = self.get_games()
            agents = self.get_agents()

            session_form = self.SessionForm()
            session_form.set_games(games)
            session_form.set_agents(agents)

            if request.method == 'POST':
                # Create the session
                session = SessionModel(
                    self.app.db(),
                    None,
                    request.form['name'],
                    request.form['game'],
                    request.form['judge'],
                    request.form['summary']
                )
                session.save()

                return redirect(url_for('session_page.sessions'))

            return render_template('session/session_new.html', session_form=session_form)

        @self.blueprint.route('/sessions/edit/<session_id>', methods=['GET', 'POST'])
        def edit_session(session_id):

            session = self.get_session(session_id)
            session_form = self.SessionForm()

            if request.method == 'POST':
                session.name = request.form['name']
                session.game = request.form['game']
                session.judge = request.form['judge']
                session.summary = request.form['summary']

                session.save()

                return redirect(url_for('session_page.view_session', session_id=session_id))

            session_form.set_session(session)
            session_form.set_agents(self.get_agents())
            session_form.set_games(self.get_games())

            return render_template('session/session_edit.html',
                                   session=session,
                                   session_form=session_form,
                                   done_form=self.DoneButtonForm()
                                   )

        @self.blueprint.route('/sessions/delete/<session_id>', methods=['GET', 'POST'])
        def delete_session(session_id):
            session = self.get_session(session_id)
            session.delete()

            return redirect(url_for('session_page.sessions'))

        @self.blueprint.route('/sessions/start/<session_id>', methods=['GET', 'POST'])
        def start_session(session_id):
            session = self.get_session(session_id)
            self.app.game().start_playing(session)
            return redirect(url_for('index_page.index'))
