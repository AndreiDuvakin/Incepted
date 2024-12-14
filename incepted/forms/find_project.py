from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField


class FindProjectForm(FlaskForm):
    project = StringField('', default='')
    submit = SubmitField('Поиск')
