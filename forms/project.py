from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField, MultipleFileField
from wtforms.validators import DataRequired


class ProjectForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    logo = FileField('Логотип')
    submit = SubmitField('Создать')
    del_photo = SubmitField('Удалить фотографию')
    save = SubmitField('Сохранить')


class AddFileProject(FlaskForm):
    file = MultipleFileField()
    submit = SubmitField('Сохранить')
