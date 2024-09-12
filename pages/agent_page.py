from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, SubmitField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, ReadOnly, Disabled

from models.agent_model import AgentModel
from pages.base_page import BasePage
from systems.game_moves import GameMoves


class AgentPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('agent_page', __name__, template_folder='pages/templates')
        self.routes()

    class AgentForm(FlaskForm):
        name = StringField('Name', validators=[DataRequired()])
        role = StringField('Role', validators=[DataRequired()])
        voice = SelectField('Voice')
        prompt = TextAreaField('Prompt', render_kw={"rows": 7})
        cancel = SubmitField('Cancel', render_kw={"formnovalidate": True})
        referrer = HiddenField('Referrer')
        submit = SubmitField('Save')

        def __init__(self, page):
            super().__init__()

            self.referrer.data = request.referrer
            self.voice.choices = [(obj.name, obj.name) for obj in page.get_voices()]

        def set_agent(self, agent):
            self.name.validators = [DataRequired(), ReadOnly(), Disabled()]
            self.name.data = agent.name
            self.role.data = agent.role
            self.voice.data = agent.voice
            self.prompt.data = agent.prompt

    class TestAgentForm(FlaskForm):
        session = SelectField('Session')
        prompt = TextAreaField('Prompt', render_kw={"rows": 7})
        send = SubmitField('Send')

        def __init__(self, page):
            super().__init__()

            self.session.choices = [(obj.id, obj.name) for obj in page.get_sessions()]

    def routes(self):
        @self.blueprint.route('/agents', methods=['GET'])
        def agents():
            return render_template('agent/agent_list.html',
                                   agents=self.get_agents(),
                                   edit_form=self.EditButtonForm(),
                                   test_form=self.TestButtonForm(),
                                   delete_form=self.DeleteButtonForm(),
                                   new_form=self.NewButtonForm()
                                   )

        @self.blueprint.route('/agent/new', methods=['GET', 'POST'])
        def new_agent():
            agent_form = self.AgentForm(self)

            if request.method == 'POST':

                if agent_form.cancel.data:
                    return redirect(request.form['referrer'])

                if agent_form.validate_on_submit():
                    agent = AgentModel(
                        self.app.db(),
                        request.form['name'],
                        request.form['prompt'],
                        request.form['voice'],
                        request.form['role']
                    )

                    agent.save()

                return redirect(url_for('agent_page.agents'))

            return render_template('agent/agent_new.html',
                                   agent_form=agent_form)

        @self.blueprint.route('/agent/edit/<agent_name>', methods=['GET', 'POST'])
        def edit_agent(agent_name):
            agent_form = self.AgentForm(self)
            agent = self.get_agent(agent_name)

            if request.method == 'POST':
                if agent_form.cancel.data:
                    return redirect(request.form['referrer'])

                if agent_form.validate_on_submit():
                    agent.prompt = request.form['prompt']
                    agent.voice = request.form['voice']
                    agent.role = request.form['role']
                    agent.save()

                return redirect(url_for('agent_page.agents'))

            agent_form.set_agent(agent)
            return render_template('agent/agent_edit.html',
                                   agent=agent,
                                   agent_form=agent_form,
                                   test_form=self.TestButtonForm(),
                                   delete_form=self.DeleteButtonForm())

        @self.blueprint.route('/agent/delete/<agent_name>', methods=['POST'])
        def delete_agent(agent_name):

            if request.method == 'POST':
                agent = self.get_agent(agent_name)
                agent.delete()

            return redirect(url_for('agent_page.agents'))

        @self.blueprint.route('/agent/test/<agent_name>', methods=['GET', 'POST'])
        def test_agent(agent_name):
            agent = self.get_agent(agent_name)
            response = None
            if not agent:
                return "Agent not found", 404

            test_agent_form = self.TestAgentForm(self)

            if request.method == 'POST':
                session_id = request.form['session']
                prompt = request.form['prompt']
                response = GameMoves(self.app, self.get_session(session_id)).get_response(agent, prompt)

            return render_template('agent/agent_test.html',
                                   agent=agent,
                                   test_agent_form=test_agent_form,
                                   edit_form=self.EditButtonForm(),
                                   response=response)
