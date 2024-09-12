from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField

from systems.system_base import SystemBase


class BasePage(SystemBase):
    def __init__(self, app):
        super().__init__(app)

    class DeleteButtonForm(FlaskForm):
        delete_button = SubmitField('Delete', render_kw={'class': 'btn btn-sm btn-danger delete-btn'})

    class EditButtonForm(FlaskForm):
        edit_button = SubmitField('Edit', render_kw={'class': 'btn btn-info btn-sm'})

    class TestButtonForm(FlaskForm):
        test_button = SubmitField('Test', render_kw={'class': 'btn btn-success btn-sm'})

    class StartButtonForm(FlaskForm):
        start_button = SubmitField('Start', render_kw={'class': 'btn btn-success btn-sm'})

    class StopButtonForm(FlaskForm):
        stop_button = SubmitField('Stop', render_kw={'class': 'btn btn-info btn-sm'})

    class NewButtonForm(FlaskForm):
        new_button = SubmitField('New', render_kw={'class': 'btn btn-info btn-sm'})

    class BackButtonForm(FlaskForm):
        back_button = SubmitField('Back', render_kw={'class': 'btn btn-info btn-sm'})

    class DoneButtonForm(FlaskForm):
        done_button = SubmitField('Done', render_kw={'class': 'btn btn-info btn-sm'})

    class StartMusicButtonForm(FlaskForm):
        start_button = SubmitField('Start Music', render_kw={'class': 'btn btn-info btn-sm'})

    class NextSongButtonForm(FlaskForm):
        next_button = SubmitField('Next Song', render_kw={'class': 'btn btn-info btn-sm'})

    class PreviousSongButtonForm(FlaskForm):
        prev_button = SubmitField('Previous Song', render_kw={'class': 'btn btn-info btn-sm'})

    class StopMusicButtonForm(FlaskForm):
        stop_button = SubmitField('Stop Music', render_kw={'class': 'btn btn-info btn-sm'})
