from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import EmailField, StringField, TextAreaField, FileField, SubmitField, DateField
from wtforms.validators import DataRequired


class EditProfileForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия')
    about = TextAreaField('Расскажите о себе', default='')
    birthday = DateField('Дата рождения')
    photo = FileField('Фото', validators=[FileAllowed(['jpg', 'png', 'bmp'], 'Только фотографии!')])
    del_photo = SubmitField('Удалить фотографию')
    submit = SubmitField('Сохранить')