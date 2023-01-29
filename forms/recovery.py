from flask_wtf import FlaskForm
from wtforms import EmailField, SubmitField, PasswordField
from wtforms.validators import DataRequired


class RecoveryForm(FlaskForm):
    email = EmailField('Введите почту для восстановления', validators=[DataRequired()])
    submit = SubmitField('Восстановить')


class NewPasswordForm(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Восстановить')
