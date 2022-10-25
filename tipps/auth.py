from dataclasses import dataclass
from typing import Optional

import flask_login
from flask import current_app, g, url_for, redirect
from werkzeug.security import check_password_hash

from .db import get_db
from .forms import LoginForm
from .model import User


def get_login_manager():
    if "login_manager " not in g:
        g.login_manager = flask_login.LoginManager()
        g.login_manager.init_app(current_app)

        @g.login_manager.user_loader
        def user_loader(id):
            return load_user_by_id(id)

        # @g.login_manager.request_loader
        def request_loader(request):
            form = LoginForm()
            if form.validate_on_submit():
                if user_id := load_user_by_token(form.token.data):
                    user = User(user_id, form.token.data)
                    return user
            return

        # @g.login_manager.unauthorized_handler
        # def unauthorized_handler():
        #     return redirect(url_for("web.login"))
        g.login_manager.login_view = "web.login"
        g.login_manager.login_message = "Bitte anmelden, um diese Seite zu betrachten."
        g.login_manager.login_message_category = "info"

    return g.login_manager


def load_user_by_id(id: int) -> Optional[User]:
    if (
        user := get_db()
        .execute("SELECT * FROM user WHERE id = ?", (id,))
        .fetchone()
    ):
        return User(**user)
    else:
        return None


def load_user_by_token(token: str) -> Optional[User]:
    if (
        user := get_db()
        .execute("SELECT * FROM user WHERE token = ?", (token,))
        .fetchone()
    ):
        return User(**user)
    else:
        return None


def load_user_by_login(name: str, password: str) -> Optional[User]:
    if (
        user := get_db()
        .execute("SELECT * FROM user WHERE LOWER(name) = LOWER(?)", (name,))
        .fetchone()
    ):
        if check_password_hash(user['password'], password):
            return User(**user)
    return None
