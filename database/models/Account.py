from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

base = declarative_base()
class Account(base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    password = Column(String(255))
    token = Column(String(255))