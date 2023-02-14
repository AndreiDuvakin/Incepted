from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, TimeField, FileField
from wtforms.validators import DataRequired


class NewTask(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    deadline_date = DateField('Дедлайн', validators=[DataRequired()])
    deadline_time = TimeField('', validators=[DataRequired()])
    submit = SubmitField('Создать')


class AnswerTask(FlaskForm):
    text = TextAreaField('Письменный ответ')
    file = FileField('Файловый ответ')
    submit = SubmitField('Ответить')
