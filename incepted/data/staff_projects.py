import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class StaffProjects(SqlAlchemyBase, UserMixin):
    __tablename__ = 'staff_projects'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer,
                             sqlalchemy.ForeignKey("users.id"), nullable=True, default=None)
    project = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("projects.id"), nullable=True, default=None)
    role = sqlalchemy.Column(sqlalchemy.Text)
    permission = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("roles.id"), nullable=True, default=None)
