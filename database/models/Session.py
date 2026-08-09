from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()
base = Base


class LoginSession(Base):
    __tablename__ = "LoginSession"

    id = Column(Integer, primary_key=True)
    userID = Column(String(255))
    device = Column(String(255))
    token = Column(String(255))
    lastLogin = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )