from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class AddLink(FlaskForm):
    link = StringField('Ссылка', validators=[DataRequired()])
    name = StringField('Название', validators=[DataRequired()])
    submit = SubmitField('Сохранить')
