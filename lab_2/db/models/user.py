from db.base import Base
from sqlalchemy import Column, String, Integer


class User(Base):
    __tablename__ = "user"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    username = Column(
        String,
        unique=True,
        nullable=False,
    )