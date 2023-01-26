import sqlalchemy
from flask_login import UserMixin
from datetime import date

from .db_session import SqlAlchemyBase


class Projects(SqlAlchemyBase, UserMixin):
    __tablename__ = 'projects'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo = sqlalchemy.Column(sqlalchemy.Text)
    date_create = sqlalchemy.Column(sqlalchemy.DateTime,
                                    default=date.today())
    creator = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"), nullable=True, default=None)
