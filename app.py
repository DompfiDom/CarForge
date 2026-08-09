import os
from datetime import timedelta

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import flask
from functools import lru_cache, wraps
import subprocess

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@lru_cache(maxsize=1)
def get_version():
    """Return the deployed revision without breaking pages when Git is unavailable."""
    configured_version = os.environ.get("APP_VERSION")
    if configured_version:
        return configured_version

    try:
        count = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=APP_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=APP_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        ).strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return None

    return f"1.0.{count} ({commit})"

load_dotenv()

app = Flask(__name__)

# Notwendig, weil Flask hinter Apache und HTTPS läuft.
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1,
)

app.config.update(
    SECRET_KEY=os.environ["FLASK_SECRET_KEY"],

    SESSION_COOKIE_NAME="carforge_session",
    SESSION_COOKIE_DOMAIN=None,
    SESSION_COOKIE_PATH="/",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",

    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

oauth = OAuth(app)

oauth.register(
    name="forgeware",
    client_id=os.environ["OIDC_CLIENT_ID"],
    client_secret=os.environ["OIDC_CLIENT_SECRET"],
    server_metadata_url=os.environ["OIDC_METADATA_URL"],
    client_kwargs={
        "scope": "openid profile email",
    },
)

@app.context_processor
def inject_version():
    return {
        "app_version": get_version()
    }

def requireLogin(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get("user") is None:
            return redirect(
                url_for(
                    "login",
                    next=flask.request.url,
                )
            )

        return function(*args, **kwargs)

    return wrapper

def requireRole(required_role):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            user = session.get("user")

            # Nicht eingeloggt: zum Login weiterleiten
            if user is None:
                return redirect(url_for("auth_login"))

            roles = user.get("roles", [])

            # Eingeloggt, aber Rolle fehlt
            if required_role not in roles:
                flask.abort(403)

            return function(*args, **kwargs)

        return wrapper

    return decorator

@app.get("/")
@requireLogin
def index():
    return flask.render_template("pages/index.html")


@app.get("/login")
def login():
    if session.get("user") is not None:
        return redirect(url_for("index"))

    return flask.render_template("login.html")

@app.route("/test")
@requireLogin
@requireRole("read.test")
def test():
    return "Das ist ein Test!"

@app.get("/impressum")
def impressum():
    return flask.render_template("impressum.html")


@app.get("/datenschutz")
def datenschutz():
    return flask.render_template("datenschutz.html")


@app.get("/auth/login")
def auth_login():
    redirect_uri = url_for(
        "auth_callback",
        _external=True,
    )

    app.logger.info("OIDC-Callback: %s", redirect_uri)

    return oauth.forgeware.authorize_redirect(
        redirect_uri,
    )


@app.get("/auth/callback")
def auth_callback():
    try:
        token = oauth.forgeware.authorize_access_token()
    except Exception as error:
        app.logger.exception("OIDC-Login fehlgeschlagen")

        return jsonify({
            "error": "OIDC-Login fehlgeschlagen",
            "details": str(error),
        }), 400

    userinfo = token.get("userinfo")

    if userinfo is None:
        userinfo = oauth.forgeware.userinfo(
            token=token,
        )

    session.clear()
    session.permanent = True

    session["user"] = {
        "id": userinfo.get("sub"),
        "username": userinfo.get("preferred_username"),
        "roles": userinfo.get("roles", []),
    }

    return redirect(
        os.environ.get(
            "FRONTEND_URL",
            "https://carforge.forgeware.de/",
        )
    )


@app.get("/api/auth/me")
def auth_me():
    user = session.get("user")

    if user is None:
        return jsonify({
            "authenticated": False,
            "user": None,
        }), 401

    return jsonify({
        "authenticated": True,
        "user": user,
    })


@app.post("/auth/logout")
def auth_logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
