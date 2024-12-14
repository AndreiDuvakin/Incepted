import sqlalchemy
from flask_login import UserMixin
from datetime import datetime

from .db_session import SqlAlchemyBase


class Quests(SqlAlchemyBase, UserMixin):
    __tablename__ = 'quests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    project = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("projects.id"), nullable=True, default=None)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True, default=None)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date_create = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())
    deadline = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())
    realized = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
