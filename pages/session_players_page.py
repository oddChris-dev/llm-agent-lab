from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired

from models.session_player_model import SessionPlayerModel
from pages.base_page import BasePage


class SessionPlayersPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('session_players_page', __name__, template_folder='pages/templates')
        self.routes()

    class AddPlayerForm(FlaskForm):
        agent = SelectField('Agent', validators=[DataRequired()])
        voice = SelectField('Voice', validators=[])
        add_player = SubmitField('Add Player')

        def set_agents(self, agents):
            agent_choices = [(agent.name, agent.name) for agent in agents]

            self.agent.choices = agent_choices

        def set_voices(self, voices):
            voice_choices = [(voice.name, voice.name) for voice in voices]
            voice_choices.insert(0, ('', 'None'))

            self.voice.choices = voice_choices

    class SessionPlayersForm(FlaskForm):
        class PlayerForm(FlaskForm):
            agent = SelectField('Agent', validators=[DataRequired()])
            voice = SelectField('Voice', validators=[])
            delete_btn = SubmitField('Remove', render_kw={'class': 'btn btn-sm btn-danger remove-btn'})

        players = FieldList(FormField(PlayerForm, label=""))
        save = SubmitField('Save')

        def fill_form(self, players, agents, voices):
            agent_choices = [(agent.name, agent.name) for agent in agents]
            voice_choices = [(voice.name, voice.name) for voice in voices]
            voice_choices.insert(0, ('', 'None'))

            for player in players:
                print(f"Adding player: {player.player}, turn_order: {player.turn_order}")  # Debugging

                self.players.append_entry({
                    'agent': player.player,  # Set agent data
                    'voice': player.voice  # Set voice data
                })

            for player_form in self.players:
                player_form.agent.choices = agent_choices
                player_form.voice.choices = voice_choices

    def routes(self):
        @self.blueprint.route('/session/<session_id>/players', methods=['GET', 'POST'])
        def session_players(session_id):
            session = self.get_session(session_id)  # Fetch session and its players
            agents = self.get_agents()  # Fetch list of agents
            voices = self.get_voices()  # Fetch list of voices

            add_player_form = self.AddPlayerForm()
            add_player_form.set_agents(agents)
            add_player_form.set_voices(voices)

            players = self.get_session_players(session_id)


            player_form = self.SessionPlayersForm()

            if request.method == 'POST':
                # Handle deleting a player
                for idx, player_entry in enumerate(player_form.players):
                    if player_entry.delete_btn.data:  # Check if the delete button was clicked
                        # Delete the player from the database
                        player_to_delete = SessionPlayerModel.get(self.app.db(), session_id, idx)
                        if player_to_delete:
                            player_to_delete.delete()

                        # Re-adjust turn orders after the delete
                        remaining_players = self.get_session_players(session_id)
                        for i, player in enumerate(remaining_players):
                            player.delete()
                            player.turn_order = i  # Re-assign turn order
                            player.save()

                        return redirect(url_for('session_players_page.session_players', session_id=session_id))

                # Handle updating existing players (without deletion)
                if player_form.save.data:
                    for idx, player_entry in enumerate(player_form.players):
                        player = SessionPlayerModel(
                            self.app.db(),
                            session_id=session_id,
                            turn_order=idx,
                            player=player_entry.agent.data,
                            voice=player_entry.voice.data
                        )
                        player.save()
                    return redirect(url_for('session_players_page.session_players', session_id=session_id))

            if len(players) > 0:
                # Fill the form with current players
                player_form.fill_form(players, agents, voices)
            else:
                player_form = None

            return render_template(
                'session/session_players.html',
                session=session,
                players=players,
                player_form=player_form,
                add_player_form=add_player_form,
                done_form=self.DoneButtonForm()
            )

        @self.blueprint.route('/session/<session_id>/players/new', methods=['POST'])
        def new_player(session_id):
            agents = self.get_agents()  # Fetch list of agents
            voices = self.get_voices()  # Fetch list of voices

            players = self.get_session_players(session_id)

            add_player_form = self.AddPlayerForm()
            add_player_form.set_agents(agents)
            add_player_form.set_voices(voices)

            if request.method == 'POST':
                # Handle adding a new player
                if add_player_form.add_player.data and add_player_form.validate_on_submit():
                    new_turn_order = len(players) + 1  # Auto-increment turn order
                    new_player = SessionPlayerModel(
                        self.app.db(),
                        session_id=session_id,
                        turn_order=new_turn_order,
                        player=add_player_form.agent.data,
                        voice=add_player_form.voice.data
                    )
                    new_player.save()

            return redirect(url_for('session_players_page.session_players', session_id=session_id))