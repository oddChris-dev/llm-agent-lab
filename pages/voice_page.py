import os
from flask import request, render_template, redirect, url_for, Blueprint, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.fields.simple import StringField, FileField, SubmitField
from wtforms.validators import DataRequired

from pages.base_page import BasePage
from systems.app import App


class VoicePage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('voice_page', __name__, template_folder='pages/templates')
        self.routes()

    class VoiceForm(FlaskForm):
        name = StringField('Voice Name', validators=[DataRequired()])
        file = FileField('Upload Voice File', validators=[FileRequired(), FileAllowed(['wav'], 'WAV files only!')])
        submit = SubmitField('Add Voice')

    def routes(self):
        @self.blueprint.route('/voices', methods=['GET'])
        def voices():
            return render_template(
                'voice/voice_list.html',
                voices=self.get_voices(),
                voice_form=self.VoiceForm(),
                delete_form=self.DeleteButtonForm(),
                test_form=self.TestButtonForm()
            )

        @self.blueprint.route('/voice/add', methods=['POST'])
        def add_voice():
            form = VoicePage.VoiceForm()
            if form.validate_on_submit():
                file = request.files['file']
                voice = self.get_voice(request.form['name'])
                voice.data = file.read()
                voice.save()
            else:
                flash(f"Invalid file format. Please upload a WAV file.", 'error')

            return redirect(url_for('voice_page.voices'))

        @self.blueprint.route('/voice/delete/<name>', methods=['POST'])
        def delete_voice(name):

            voice = self.get_voice(name)

            if voice:
                voice.delete()

            return redirect(url_for('voice_page.voices'))

        @self.blueprint.route('/say', methods=['POST'])
        def say():
            """Say a prompt with the selected voice."""
            prompt = request.form['prompt']
            voice = request.form['voice']
            App.config.default_voice = voice
            self.app.speech().voice_say(voice, prompt)
            return redirect(request.referrer or url_for('index_page.index'))

