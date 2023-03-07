from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, TimeField, MultipleFileField, \
    BooleanField
from wtforms.validators import DataRequired


class Task(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    deadline_date = DateField('Дедлайн')
    deadline_time = TimeField('')
    submit = SubmitField('Создать')
    save = SubmitField('Сохранить')
    delete = SubmitField('Удалить')


class AnswerTask(FlaskForm):
    text = TextAreaField('Письменный ответ')
    file = MultipleFileField('Добавить файлы')
    realized = BooleanField('Задача решена')
    submit = SubmitField('Сохранить')
