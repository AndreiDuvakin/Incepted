from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class DeleteProjectForm(FlaskForm):
    conf = StringField('', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
