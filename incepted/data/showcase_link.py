import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class ShowCaseLink(SqlAlchemyBase, UserMixin):
    __tablename__ = 'showcase_link'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    link = sqlalchemy.Column(sqlalchemy.Text, nullable=True, default=None)
    name = sqlalchemy.Column(sqlalchemy.Text, nullable=True, default=None)
    user = sqlalchemy.Column(sqlalchemy.Integer,
                             sqlalchemy.ForeignKey("users.id"), nullable=True, default=None)
    up_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
