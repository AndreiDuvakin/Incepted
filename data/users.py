from datetime import date

import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, nullable=False)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo = sqlalchemy.Column(sqlalchemy.Text)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    data_reg = sqlalchemy.Column(sqlalchemy.Date,
                                 default=date.today())
    role = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    activity = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    birthday = sqlalchemy.Column(sqlalchemy.Date, nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)
