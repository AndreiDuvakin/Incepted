import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class Files(SqlAlchemyBase, UserMixin):
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    path = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    user = sqlalchemy.Column(sqlalchemy.Integer,
                             sqlalchemy.ForeignKey("users.id"), nullable=True, default=None)
    up_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
