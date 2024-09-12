from flask import request, render_template, redirect, url_for, Blueprint
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired

from models.session_setting_model import SessionSettingModel
from pages.base_page import BasePage


class SessionSettingsPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('session_settings_page', __name__, template_folder='pages/templates')
        self.routes()

    # Form for adding a new setting
    class AddSettingForm(FlaskForm):
        setting_name = StringField('Name', validators=[DataRequired()])
        setting_value = StringField('Value', validators=[DataRequired()])
        submit = SubmitField('Add Setting', render_kw={'class': 'btn btn-info btn-sm'})

    # Form for editing/deleting existing settings
    class EditSettingForm(FlaskForm):
        setting_value = StringField('', validators=[DataRequired()])
        submit = SubmitField('Save', render_kw={'class': 'btn btn-info btn-sm'})

        def set_setting(self, setting):
            self.setting_value.data = setting.value
            return ""

    def routes(self):
        @self.blueprint.route('/session/<session_id>/settings', methods=['GET', 'POST'])
        def session_settings(session_id):
            session = self.get_session(session_id)
            add_form = self.AddSettingForm()

            # Handle the POST request for adding a new setting
            if add_form.validate_on_submit():
                setting = SessionSettingModel(
                    self.app.db(),
                    session_id,
                    add_form.setting_name.data,
                    add_form.setting_value.data
                )
                setting.save()
                return redirect(url_for('session_settings_page.session_settings', session_id=session_id))

            # Get all session settings for the session
            settings = self.get_session_settings(session_id)

            return render_template('session/session_settings.html',
                                   session=session,
                                   done_form=self.DoneButtonForm(),
                                   add_form=add_form,
                                   settings=settings,
                                   delete_form=self.DeleteButtonForm(),
                                   edit_form=self.EditSettingForm())

        @self.blueprint.route('/session/<session_id>/setting/edit/<setting_name>', methods=['POST'])
        def edit_setting(session_id, setting_name):
            setting = self.get_session_setting(session_id, setting_name)
            form = self.EditSettingForm()

            if form.validate_on_submit():
                setting.value = request.form['setting_value']
                setting.save()

            return redirect(url_for('session_settings_page.session_settings', session_id=session_id))

        @self.blueprint.route('/session/<session_id>/setting/delete/<setting_name>', methods=['POST'])
        def delete_setting(session_id, setting_name):
            setting = self.get_session_setting(session_id, setting_name)
            setting.delete()

            return redirect(url_for('session_settings_page.session_settings', session_id=session_id))
