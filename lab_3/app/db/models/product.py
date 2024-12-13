from sqlalchemy import Column, Integer, String, Float
from db.base import Base


class Product(Base):
    __tablename__ = "product"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name = Column(
        String,
        nullable=False,
    )
    price = Column(
        Float,
        nullable=False,
    )
    specifications = Column(
        String,
        nullable=True,
    )