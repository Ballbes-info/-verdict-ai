import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users_table'
    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    google_id = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    avatar = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.utcnow)