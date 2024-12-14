from flask_wtf import FlaskForm
from wtforms import BooleanField


class EggForm(FlaskForm):
    egg = BooleanField('Пасхалка')