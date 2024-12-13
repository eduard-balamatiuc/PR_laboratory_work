import os
from db.base import Base
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")

engine = create_engine(DATABASE_URL)
session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def init_db():
    from db.models.product import Product
    Base.metadata.create_all(bind=engine)