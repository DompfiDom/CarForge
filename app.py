import database.database as database
import flask
from flask import request, jsonify, make_response
import bcrypt
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix


app = flask.Flask(__name__)

# Mache die App "proxy-aware".
# Dies ist der entscheidende Schritt, damit Flask die X-Forwarded-Header von Apache
# korrekt interpretiert (z.B. dass die Anfrage über HTTPS kam).
# Ohne dies können sichere Cookies im Live-Betrieb fehlschlagen.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# CORS für API-Routen aktivieren. WICHTIG: `supports_credentials=True` ist für Cookies erforderlich.
# Der Origin '*' ist mit `supports_credentials` nicht erlaubt. Er muss auf den Frontend-Host gesetzt werden.
allowed_origins = [
    "http://localhost:5173",  # Vite default dev server
    "https://orbitalflux.forgeware.de" # Deine Produktions-Domain
]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

app.secret_key = 'setze-hier-einen-sehr-geheimen-und-langen-text-ein'


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Benutzername und Passwort sind erforderlich"}), 400

    username = data.get('username')
    password = data.get('password')

    account = database.validateCredentials(username)

    if account and bcrypt.checkpw(password.encode(), account.password.encode()):
        token, user_id = database.setToken(username)
        resp = make_response(jsonify({"message": "Login erfolgreich", "userId": user_id}), 200)

        # Setze den Token in einem sicheren, HttpOnly-Cookie.
        # Der Browser wird diesen Cookie automatisch bei jeder nachfolgenden Anfrage an den Server mitsenden.
        # JavaScript kann nicht darauf zugreifen, was XSS-Angriffe zur Token-Entwendung verhindert.
        resp.set_cookie(
            'session_token',
            value=token,
            httponly=True,  # Verhindert JavaScript-Zugriff
            samesite='Lax', # Bietet Schutz gegen CSRF-Angriffe
            # `secure=True` in Produktion (wenn app.debug=False), damit Cookies nur über HTTPS gesendet werden.
            secure=not app.debug
        )
        return resp
    else:
        return jsonify({"error": "Ungültiger Benutzername oder Passwort"}), 401

@app.route('/api/check-session', methods=['GET'])
def check_session():
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({"error": "Keine aktive Session gefunden"}), 401

    account = database.getUserByToken(token)

    if account:
        # Die Session ist gültig. Sende die Benutzerdaten zurück.
        return jsonify({"message": "Session ist valide", "userId": account.id, "username": account.username}), 200
    else:
        return jsonify({"error": "Ungültige Session"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({"message": "Logout erfolgreich"}), 200)
    # Lösche das Cookie, indem ein leeres Cookie mit einem abgelaufenen Datum gesetzt wird.
    resp.set_cookie('session_token', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)