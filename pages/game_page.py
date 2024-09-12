import json

from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Disabled, ReadOnly

from models.game_model import GameModel
from pages.base_page import BasePage


class GamePage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('game_page', __name__, template_folder='pages/templates')
        self.routes()

    class GameForm(FlaskForm):
        name = StringField('Name', validators=[DataRequired()])
        rules = TextAreaField('Rules', validators=[DataRequired()], render_kw={"rows": 7})
        variables = TextAreaField('Default Settings', validators=[DataRequired()], render_kw={"rows": 7}, default="{}")
        submit = SubmitField('Save')

        def set_game(self, game):
            self.name.data = game.name
            self.rules.data = game.rules
            self.variables.data = json.dumps(game.variables, indent=2)

    def routes(self):
        @self.blueprint.route('/games', methods=['GET'])
        def games():
            return render_template('game/game_list.html',
                                   games=self.get_games(),
                                   edit_form=self.EditButtonForm(),
                                   delete_form=self.DeleteButtonForm(),
                                   new_form=self.NewButtonForm()
                                   )

        @self.blueprint.route('/game/new', methods=['GET', 'POST'])
        def new_game():
            if request.method == 'POST':
                game = GameModel(
                    self.app.db(),
                    request.form['name'],
                    request.form['rules'],
                    json.loads(request.form['variables'])
                )
                game.save()

                return redirect(url_for('game_page.games'))

            return render_template('game/game_new.html', game_form=self.GameForm())

        @self.blueprint.route('/game/edit/<game_name>', methods=['GET', 'POST'])
        def edit_game(game_name):
            game = self.get_game(game_name)

            if request.method == 'POST':
                game.rules = request.form['rules']
                game.variables = json.loads(request.form['variables'])
                game.save()

                return redirect(url_for('game_page.games'))

            game_form = self.GameForm()
            game_form.set_game(game)
            return render_template(
                'game/game_edit.html',
                game=game,
                game_form=game_form
            )

        @self.blueprint.route('/game/delete/<game_name>', methods=['GET', 'POST'])
        def delete_game(game_name):
            game = self.get_game(game_name)
            game.delete()

            return redirect(url_for('game_page.games'))
