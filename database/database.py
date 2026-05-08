import os
import random
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import bcrypt

from database.models.Account import Account

# Lade die Datenbank-URL aus einer Umgebungsvariable.
# Standardmäßig wird die MySQL-URL verwendet, die Sie zuvor konfiguriert hatten.
#mysql+pymysql://orbital_flux:fgeg445rgrehgd4ezhjetgw(/%tzuztujkkt&=?$%G4dd6dd78REERG@localhost:3306/orbital_flux
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://mysql:jLAeTpSW3qNROJlJePTBEw99N2yKDYwKkMF8SsJhi0cnKwIAse0JiUHpi5ZDw6eA@f3u3wnu5z7h628bi3g5f8w22:3306/default",
)
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create tables with error handling for existing tables
try:
    Account.metadata.create_all(engine)

except Exception as e:
    print(f"Warning: Some tables may already exist: {e}")

Session = sessionmaker(bind=engine)

def getSession():
    # Erstelle immer eine neue Session für jeden Request
    return Session()

def closeSession(session):
    try:
        session.close()
    except:
        pass

def createAccount(username, password):
    session = getSession()
    try:
        account = Account()
        account.username = username
        account.token = "#"
        account.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        session.add(account)
        session.commit()
        session.flush()
    finally:
        closeSession(session)

def validateCredentials(username):
    session = getSession()
    try:
        # .first() ist effizienter und korrekter als eine Schleife
        account = session.query(Account).filter(Account.username == str(username)).first()
        if account:
            return account
        return None
    finally:
        closeSession(session)

def getUserByToken(token):
    session = getSession()
    try:
        if not token:
            return None
        # Find the account by the session token
        account = session.query(Account).filter(Account.token == str(token)).first()
        return account
    finally:
        closeSession(session)

def validateUserSession(username, token):
    if token == "MASTER":
        return True
    
    if not username or not token:
        return False

    session = getSession()
    try:
        # .first() ist effizienter und korrekter
        account = session.query(Account).filter(Account.username == str(username)).first()
        return bool(account and str(account.token) == str(token))
    finally:
        closeSession(session)

def resetToken(username):
    session = getSession()
    try:
        session.query(Account).filter(Account.username == username).update({"token": "#"})
        session.commit()
    finally:
        closeSession(session)

def setToken(username):
    session = getSession()
    try:
        ran = random.randint(10000000, 99999999)
        token = bcrypt.hashpw(str(ran).encode(), bcrypt.gensalt()).decode()
        item = session.query(Account).filter(Account.username == username).first()
        if item:
            item.token = token
        else:
            account = Account()
            account.username = username
            account.token = token
            account.password = bcrypt.hashpw(b"discord_oauth_dummy", bcrypt.gensalt()).decode()
            session.add(account)
        session.commit()
        return token, getUserIDByName(username)
    finally:
        closeSession(session)

def userExists(username):
    session = getSession()
    try:
        return session.query(Account).filter(Account.username == username).count() > 0
    finally:
        closeSession(session)
        
def getUserIDByName(username):
    session = getSession()
    try:
        user = session.query(Account).filter(Account.username == username).first()
        return user.id if user else None
    finally:
        closeSession(session)

def updateUserPassword(user_id, new_password):
    session = getSession()
    try:
        # Da die User-ID (Discord-ID) je nach Implementierung in id oder username steht,
        # suchen wir sicherheitshalber in beiden Feldern.
        user = session.query(Account).filter(Account.id == user_id).first()
        if not user:
            user = session.query(Account).filter(Account.username == str(user_id)).first()
        if user:
            user.password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            session.commit()
            return True
        return False
    finally:
        closeSession(session)

def verifyToken(token, id):
    session = getSession()
    try:
        user = session.query(Account).filter(Account.id == id).first()
        result = bcrypt.checkpw(token.encode(), user.password.encode())
        return result, user.username
    finally:
        closeSession(session)