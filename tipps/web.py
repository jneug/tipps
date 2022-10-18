from pathlib import Path

from flask import (Blueprint, abort, current_app, g, redirect, render_template,
                   request, send_file, url_for)

from tipps.db import get_db
from tipps.util import *

web = Blueprint("web", __name__)


@web.route("/", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        code = request.form.get("code", default=None, type=str)
        if code:
            return redirect(url_for("web.show_tipp", id=code), 303)
        return render_template(
            "index.html",
            error="Zu deinem Code konnten wir leider keinen Tipp finden. Hast du dich vielleicht vertippt? Versuch es ruhig noch einmal.",
        )
    else:
        return render_template("index.html")


@web.route("/list")
def list():
    token = "webfij23h87revb03fbre"

    db = get_db()
    result = db.execute(
        f'SELECT tipp.id,tipp.created,tipp.template FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = "{token}" ORDER BY tipp.created DESC'
    ).fetchall()

    tipps = []
    for row in result:
        tipps.append(
            {
                "id": row["id"],
                "title": get_tipp_title(row["id"]),
                "excerpt": get_tipp_excerpt(row["id"]),
                "url": get_tipp_url(row["id"]),
                "qrurl": get_qr_url(row["id"]),
                "created": row["created"],
                "template": row["template"],
            }
        )
    return render_template("list.html", tipps=tipps)


@web.route("/edit/<string:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        content = request.form.get("content", default="", type=str)
        token = request.form.get("token", default="", type=str)
        template = request.form.get("template", default="default", type=str)

        if len(content.strip()) == 0 or len(token.strip()) == 0:
            return render_template(
                "input.html",
                form={
                    "type": "create",
                    "token": token,
                    "templates": get_templates(),
                    "error": "Inhalt und Token dürfen nicht leer sein.",
                },
                tipp={"content": content, "template": template},
            )

        db = get_db()
        user_id = db.execute("SELECT id FROM user WHERE token = ?", (token,)).fetchone()
        if not user_id:
            return render_template(
                "input.html",
                form={
                    "type": "create",
                    "token": token,
                    "templates": get_templates(),
                    "error": "Kein gültiges Token.",
                },
                tipp={"content": content, "template": template},
            )

        timestamp = update_tipp(id, content, template=template)

        db.execute(
            "UPDATE tipp SET compiled = ?, template = ? WHERE id = ?",
            (
                timestamp,
                template,
                id,
            ),
        )
        db.commit()

        return redirect(url_for("web.show_tipp", id=id), 303)
    else:
        token = "webfij23h87revb03fbre"

        db = get_db()
        result = db.execute(
            "SELECT tipp.* FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE tipp.id = ? AND user.token = ?",
            (
                id,
                token,
            ),
        ).fetchone()

        form = {"type": "edit", "token": token, "templates": get_templates()}

        tipp = dict(result)
        if result:
            tipp["content"] = get_tipp_content(id)
        else:
            tipp["content"] = ""
            tipp["template"] = "default"
            form["error"] = "Kein Tipp mit der angegebenen ID gefunden."

        return render_template("input.html", form=form, tipp=tipp)


@web.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        content = request.form.get("content", default="", type=str)
        token = request.form.get("token", default="", type=str)
        template = request.form.get("template", default="default", type=str)

        if len(content.strip()) == 0 or len(token.strip()) == 0:
            return render_template(
                "input.html",
                form={
                    "type": "create",
                    "token": token,
                    "templates": get_templates(),
                    "error": "Inhalt und Token dürfen nicht leer sein.",
                },
                tipp={"content": content, "template": template},
            )

        db = get_db()
        user_id = db.execute("SELECT id FROM user WHERE token = ?", (token,)).fetchone()
        if not user_id:
            return render_template(
                "input.html",
                form={
                    "type": "create",
                    "token": token,
                    "templates": get_templates(),
                    "error": "Kein gültiges Token.",
                },
                tipp={"content": content, "template": template},
            )

        id = create_tipp(content, template=template)

        db.execute(
            "INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)",
            (
                id,
                user_id["id"],
                template,
            ),
        )
        db.commit()

        return redirect(url_for("web.show_tipp", id=id), 303)
    else:
        return render_template(
            "input.html", form={"type": "create", "templates": get_templates()}, tipp={}
        )


@web.route("/<string:id>")
def show_tipp(id):
    page_path = Path(current_app.config["PAGEPATH"]) / f"{id}.html"
    if page_path.is_file():
        return send_file(page_path, mimetype="text/html")
    else:
        abort(404)


@web.route("/qr/<string:id>")
def show_qr(id):
    qr_path = Path(current_app.config["QRPATH"]) / f"{id}.png"
    if qr_path.is_file():
        return send_file(qr_path, mimetype="image/png")
    else:
        abort(404)
