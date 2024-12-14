import sqlalchemy
from flask_login import UserMixin
from datetime import datetime

from .db_session import SqlAlchemyBase


class FileProof(SqlAlchemyBase, UserMixin):
    __tablename__ = 'file_proof'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    answer = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("answer.id"), nullable=True, default=None)
    file = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("files.id"), nullable=True, default=None)
