from flask_wtf import FlaskForm
from wtforms import SubmitField


class EncryptForm(FlaskForm):
    submit = SubmitField('Сохранить')
