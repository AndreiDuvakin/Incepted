from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, FileField, MultipleFileField, BooleanField
from wtforms.validators import DataRequired


class ProjectForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    logo = FileField('Логотип', validators=[FileAllowed(['jpg', 'png', 'bmp', 'ico', 'jpeg'], 'Только изображения')])
    is_template = BooleanField('Шаблон')
    submit = SubmitField('Создать')
    del_photo = SubmitField('Удалить фотографию')
    save = SubmitField('Сохранить')


class AddFileProject(FlaskForm):
    file = MultipleFileField()
    submit = SubmitField('Сохранить')
