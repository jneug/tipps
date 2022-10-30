import re
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    flash,
    session,
)
import flask_login

from .db import get_db
from .auth import LoginForm, load_user_by_login
from .model import Template, Tipp, User, Pagination
from .forms import ConfirmDeleteForm, FilterForm

web = Blueprint("web", __name__)


@web.route("/", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        code = request.form.get("code", default=None, type=str)
        if code:
            return redirect(url_for("web.show_tipp", id=code), 303)
    if "tipp-id" in session:
        code = session.pop("tipp-id", None)
        flash(f"Zu deinem Code <strong>{code}</strong> konnten wir leider keinen Tipp finden. Hast du dich vielleicht vertippt? Versuch es ruhig noch einmal.", "warning")
    return render_template("index.html", id="")


@web.route("/login", methods=["GET", "POST"])
def login():
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("web.list"))

    form = LoginForm()
    if form.validate_on_submit():
        print("valid")
        if user := load_user_by_login(form.username.data, form.password.data):
            flask_login.login_user(user, remember=current_app.config["REMEMBER_USER"])
            if flask_login.current_user.is_authenticated:
                flash("Erfolgreich angemeldet.", "success")
                return redirect(url_for("web.list"))
        flash("Fehler bei der Anmeldung.", "error")
    return render_template("login.html", form=LoginForm())


@web.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect(url_for("web.start"))


@web.route("/list")
@flask_login.login_required
def list():
    token = flask_login.current_user.token
    query_data = [token]

    filter_form = FilterForm(formdata=request.args)
    filter_form.template.choices = Template.get_template_names()

    sort = "created" if filter_form.sort.data == "created" else "compiled"

    tpl_filter = ""
    if filter_form.template.data:
        tpl_filter = " AND template = ?"
        query_data.append(filter_form.template.data)

    db = get_db()
    if filter_form.search.data:
        result = db.execute(
            f"SELECT tipp.* FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = ?{tpl_filter} ORDER BY tipp.{sort} DESC",
            tuple(query_data)
        ).fetchall()

        re_search = re.compile(re.escape(filter_form.search.data), flags=re.IGNORECASE)

        tipps = []
        for row in result:
            _tipp = Tipp(**row)
            # if filter_form.search.data in _tipp.raw_content:
            if re_search.search(_tipp.raw_content):
                tipps.append(_tipp)

        pagination = Pagination(per_page=21, items=len(tipps))
        print(f"{pagination.first_item=}:{pagination.last_item=}")
        tipps = tipps[pagination.first_item:pagination.last_item]
    else:
        result = db.execute(
            f"SELECT COUNT(*) FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = ?{tpl_filter}",
            tuple(query_data),
        ).fetchone()

        pagination = Pagination(per_page=21, items=int(result[0]))
        query_data.append(pagination.per_page)
        query_data.append(pagination.first_item)

        result = db.execute(
            f"SELECT tipp.* FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = ?{tpl_filter} ORDER BY tipp.{sort} DESC LIMIT ? OFFSET ?",
            tuple(query_data)
        ).fetchall()

        tipps = [Tipp(**row) for row in result]

    return render_template(
        "list.html",
        tipps=tipps,
        pagination=pagination,
        form=ConfirmDeleteForm(),
        filter=filter_form
    )


@web.route("/edit/<string:id>", methods=["GET", "POST"])
@flask_login.login_required
def edit(id):
    token = flask_login.current_user.token

    if request.method == "POST":
        content = request.form.get("content", default="", type=str)
        token = request.form.get("token", default=token, type=str)
        template = request.form.get("template", default="default", type=str)

        if len(content.strip()) == 0 or len(token.strip()) == 0:
            return render_template(
                "edit.html",
                form={
                    "type": "create",
                    "token": token,
                    "templates": Template.get_templates(),
                    "error": "Inhalt und Token dürfen nicht leer sein.",
                },
                tipp={"content": content, "template": template},
            )

        db = get_db()
        tipp = Tipp(id, template=template)
        tipp.save(content)

        db.execute(
            "UPDATE tipp SET compiled = ?, template = ? WHERE id = ?",
            (
                tipp.compiled,
                template,
                tipp.id,
            ),
        )
        db.commit()

        return redirect(url_for("web.show_tipp", id=tipp.id), 303)
    else:
        db = get_db()
        result = db.execute(
            "SELECT tipp.* FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE tipp.id = ? AND user.token = ?",
            (
                id,
                token,
            ),
        ).fetchone()

        form = {"type": "edit", "token": token, "templates": Template.get_templates()}

        tipp = Tipp(**result)
        if not tipp.exists():
            form["error"] = "Kein Tipp mit der angegebenen ID gefunden."

        return render_template("edit.html", form=form, tipp=tipp)


@web.route("/create", methods=["GET", "POST"])
@flask_login.login_required
def create():
    token = flask_login.current_user.token

    if request.method == "POST":
        content = request.form.get("content", default="", type=str)
        token = request.form.get("token", default=token, type=str)
        template = request.form.get("template", default="default", type=str)

        if len(content.strip()) == 0 or len(token.strip()) == 0:
            return render_template(
                "edit.html",
                form={
                    "type": "create",
                    "token": token,
                    "templates": Template.get_templates(),
                    "error": "Inhalt und Token dürfen nicht leer sein.",
                },
                tipp={"content": content, "template": template},
            )

        db = get_db()
        tipp = Tipp(template=template)
        tipp.save(content)

        db.execute(
            "INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)",
            (
                tipp.id,
                flask_login.current_user.id,
                template,
            ),
        )
        db.commit()

        return redirect(url_for("web.show_tipp", id=tipp.id), 303)
    else:
        return render_template(
            "edit.html",
            form={"type": "create", "templates": Template.get_templates()},
            tipp={},
        )


@web.route("/delete", methods=["POST"])
@flask_login.login_required
def delete():
    back = request.referrer or url_for('web.list')

    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        if form.submit.data:
            tipp = Tipp(form.tipp.data)
            tipp.delete()

            db = get_db()
            db.execute("DELETE FROM tipp WHERE id = ?", (tipp.id,))
            db.commit()

            flash(f"Tipp <strong>{tipp.id}</strong> gelöscht.", "success")
            return redirect(back)
    flash("Ein Fehler ist aufgetreten. Es wurden keine Daten gelöscht.", "error")
    return redirect(back)


@web.route("/<string:id>")
def show_tipp(id):
    tipp = Tipp(id)
    if tipp.page_path.is_file():
        if current_app.config['DEBUG'] and tipp.exists():
            _tipp = get_db().execute("SELECT * FROM tipp WHERE id = ?", (tipp.id,)).fetchone()
            if _tipp:
                tipp = Tipp(**_tipp)
                current_app.logger.info(f"Compiling tipp {tipp.id} in debug mode")
                tipp.compile()
        return send_file(tipp.page_path, mimetype="text/html")
    else:
        session['tipp-id'] = id
        return redirect(url_for("web.start"))


@web.route("/qr/<string:id>")
def show_qr(id):
    tipp = Tipp(id)
    if tipp.qr_path.is_file():
        return send_file(tipp.qr_path, mimetype="image/png")
    else:
        abort(404)
