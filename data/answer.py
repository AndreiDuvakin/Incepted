import sqlalchemy
from flask_login import UserMixin
from datetime import datetime

from .db_session import SqlAlchemyBase


class Answer(SqlAlchemyBase, UserMixin):
    __tablename__ = 'answer'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    quest = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("quests.id"), nullable=True, default=None)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=True, default=None)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True,
                                default=None)
    date_create = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())
    date_edit = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())
