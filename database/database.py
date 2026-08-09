import os
import secrets
import json
import uuid
from datetime import datetime, timezone

import bcrypt
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from database.models.Account import Account
from database.models.Session import LoginSession


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://authentification:)OW3Y/0E0[7D)wRT@localhost:3306/authentification",
)
engine = sqlalchemy.create_engine(DATABASE_URL)
Account.metadata.create_all(engine)
LoginSession.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def checkUserCredentials(username, password):
    with Session() as session:
        item = session.query(Account).filter(Account.username == str(username)).first()
        if item == None:
            return False
        result = bcrypt.checkpw(password.encode(), item.password.encode())
        return result
    return False

def setToken(username, device):
    with Session() as session:
        account = (
            session.query(Account)
            .filter(Account.username == str(username))
            .first()
        )

        if account is None:
            return False

        token = str(uuid.uuid4())

        loginSession = LoginSession()
        loginSession.userID = account.id
        loginSession.device = device
        loginSession.token = token
        loginSession.lastLogin = datetime.now(timezone.utc)
        session.add(loginSession)
        session.commit()
        return token

def getUserID(username):
    with Session() as session:
        account = (
            session.query(Account)
            .filter(Account.username == str(username))
            .first()
        )  
        return account.id

def checkUserSession(username, token):
    userID = getUserID(username)
    with Session() as session:
        items = (
            session.query(LoginSession)
            .filter(LoginSession.userID == str(userID))
            .all()
        )

        for item in items:
            if token == item.token:
                item.lastLogin = datetime.now(timezone.utc)
                session.commit()
                return True
        return False
