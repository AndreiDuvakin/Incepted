from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import EmailField, StringField, PasswordField, SubmitField, FileField, DateField, TextAreaField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Регистрация')