from functools import wraps
from pathlib import Path
from dataclasses import asdict

from flask import Blueprint, current_app, g, request
import flask_login

from tipps.db import get_db
from tipps.model import Template, Tipp


ACCEPTED_MIMETYPES = [
    "application/json",
    "application/x-www-form-urlencoded",
    "text/plain"
]


v1 = Blueprint("api/v1", __name__, url_prefix="/api/v1")


@v1.route("/tipps")
@v1.route("/tokens/<string:token>/tipps")
def list_tipps(token=None):
    details = request.args.get("details", default=False, type=bool)

    sort = request.args.get("sort", default="created_desc", type=str).lower().split("_")
    if sort[0] == "rand":
        sort[0] = "RANDOM()"
    elif sort[0] not in ["created", "compiled", "id"]:
        sort[0] = "tipp.created"
    else:
        sort[0] = f"tipp.{sort[0]}"
    if len(sort) < 2:
        sort.append("asc")
    elif sort[1] not in ["asc", "desc"]:
        sort[1] = "asc"
    sort = f"{sort[0]} {sort[1].upper()}"

    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)

    # filters
    filters = {}

    template = request.args.get("template", default=None)
    if template:
        filters["tipp.template"] = template
    if token:
        filters["user.token"] = token

    if len(filters) > 0:
        where = " WHERE " + ", ".join([f"{k} = ?" for k in filters.keys()])
    else:
        where = ""

    db = get_db()
    result = db.execute(
        f"SELECT tipp.* FROM tipp INNER JOIN user ON user.id = tipp.user_id{where} ORDER BY {sort} LIMIT {limit} OFFSET {offset}",
        tuple(filters.values()),
    ).fetchall()

    tipps = []
    if result:
        for row in result:
            tipp = Tipp(**row)
            if not details:
                tipps.append(tipp.id)
            else:
                tipps.append(
                    {
                        "id": tipp.id,
                        "url": tipp.url,
                        "qrurl": tipp.qr_url,
                        "created": tipp.created,
                        "compiled": tipp.compiled,
                        "template": tipp.template.name,
                    }
                )
    return {"tipps": tipps}


@v1.route("/templates")
def list_templates():
    # list template files in templates folder
    # perhaps makes sense to move the tipp templates to another folder
    # e.g. assets/templates
    templates = Template.get_template_names()
    return {"templates": sorted(templates)}


@v1.route("/tipps/<string:id>")
def tipp_details(id):
    db = get_db()

    result = db.execute("SELECT * FROM tipp WHERE id = ?", (id,)).fetchone()
    if result:
        _tipp = Tipp(**result)
        tipp = {
            "id": _tipp.id,
            "created": _tipp.created,
            "compiled": _tipp.compiled,
            "template": _tipp.template.name,
            "url": _tipp.url,
            "qrurl": _tipp.qr_url,
            "content": _tipp.raw_content,
        }

        return tipp
    else:
        return ({"error": 404, "msg": "unknown id"}, 404)


@v1.route("/tipps/<string:id>", methods=["PUT"])
def tipp_update(id):
    if request.mimetype not in ACCEPTED_MIMETYPES:
        return (
            {"code": 400, "msg": "missing content type"},
            400,
            {"Accept": ','.join(ACCEPTED_MIMETYPES)},
        )

    if request.is_json:
        content = str(request.json.get("content", ""))
        template = str(request.json.get("template", "default"))
    elif request.mimetype == "application/x-www-form-urlencoded":
        content = request.form.get("content", default="", type=str)
        template = request.form.get("template", default="default", type=str)
    elif request.mimetype == "text/plain":
        content = request.data.decode().strip()
        template = "default"
    else:
        return (
            {"code": 415, "msg": "unsupported content type"},
            415,
            {"Accept": ','.join(ACCEPTED_MIMETYPES)},
        )

    charset = request.mimetype_params.get("charset", "utf-8")
    if charset != "utf-8":
        content = content.encode(charset).decode()
        template = template.encode(charset).decode()

    if len(content.strip()) == 0:
        return ({"code": 400, "msg": "content may not be empty"}, 400)

    tipp = Tipp(id, template=template)
    tipp.save(content)

    db = get_db()
    db.execute(
        "UPDATE tipp SET compiled = ?, template = ? WHERE id = ?",
        (
            tipp.compiled,
            tipp.template.name,
            tipp.id,
        ),
    )
    db.commit()

    return ({
        "id": tipp.id,
        "compiled": tipp.compiled,
        "template": tipp.template.name
    }, 200)


@v1.route("/tipps/<string:id>", methods=["PATCH"])
def tipp_compile(id):
    db = get_db()
    result = db.execute("SELECT * FROM tipp WHERE id = ?", (id,)).fetchone()
    if result:
        tipp = Tipp(**result)
        # TODO: allow form-date / plaintext here?
        tipp.template = Template(request.json.get("template", tipp.template))
        tipp.compile()
        db.execute(
            "UPDATE tipp SET compiled = ?, template = ? WHERE id = ?",
            (
                tipp.compiled,
                tipp.template.name,
                tipp.id,
            ),
        )
        db.commit()

        return ({
            "id": tipp.id,
            "compiled": tipp.compiled,
            "template": tipp.template.name
        }, 200)
    else:
        return ({"code": 400, "msg": "unknown id"}, 400)


@v1.route("/tipps/<string:id>", methods=["DELETE"])
@flask_login.login_required
def tipp_delete(id):
    db = get_db()
    result = db.execute("SELECT * FROM tipp WHERE id = ?", (id,)).fetchone()
    tipp = Tipp(**result)

    if not result:
        return ({"code": 404, "msg": "unknown id"}, 404)
    if tipp.user_id != flask_login.current_user.id:
        return ({"code": 403, "msg": "tipp owned by other user"}, 403)

    db.execute(
        "DELETE FROM tipp WHERE id = ? AND user_id = ?",
        (
            tipp.id,
            flask_login.current_user.id,
        ),
    )
    db.commit()

    # remove files
    tipp.delete()

    return ("", 204)


@v1.route("/tipps", methods=["POST"])
@flask_login.login_required
def tipp_create():
    if request.mimetype not in ACCEPTED_MIMETYPES:
        return (
            {"code": 400, "msg": "missing content type"},
            400,
            {"Accept": ','.join(ACCEPTED_MIMETYPES)},
        )

    if request.is_json:
        content = str(request.json.get("content", ""))
        template = str(request.json.get("template", "default"))
    elif request.mimetype == "application/x-www-form-urlencoded":
        content = request.form.get("content", default="", type=str)
        template = request.form.get("template", default="default", type=str)
    elif request.mimetype == "text/plain":
        content = request.data.decode().strip()
        template = "default"
    else:
        return (
            {"code": 415, "msg": "unsupported content type"},
            415,
            {"Accept": ','.join(ACCEPTED_MIMETYPES)},
        )

    charset = request.mimetype_params.get("charset", "utf-8")
    if charset != "utf-8":
        content = content.encode(charset).decode()
        template = template.encode(charset).decode()

    if len(content.strip()) == 0:
        return ({"code": 400, "msg": "content may not be empty"}, 400)

    tipp = Tipp()
    tipp.template = Template(template)
    tipp.save(content)

    db = get_db()
    db.execute(
        "INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)",
        (
            tipp.id,
            flask_login.current_user.id,
            tipp.template.name,
        ),
    )
    db.commit()

    return (
        {
            "id": id,
            "created": tipp.created,
            "compiled": tipp.compiled,
            "template": tipp.template.name,
            "url": tipp.url,
            "qrurl": tipp.qr_url,
            "content": tipp.raw_content,
        },
        201,
    )


# @v1.route("/tokens", methods=["POST"])
# @flask_login.login_required
# def token_create():
#     if request.mimetype not in ACCEPTED_MIMETYPES:
#         return (
#             {"code": 400, "msg": "missing content type"},
#             400,
#             {"Accept": ','.join(ACCEPTED_MIMETYPES)},
#         )

#     if request.is_json:
#         name = str(request.json.get("name", ""))
#     elif request.mimetype == "application/x-www-form-urlencoded":
#         name = request.form.get("name", default="", type=str)
#     elif request.mimetype == "text/plain":
#         name = request.data.decode().strip()
#     else:
#         return (
#             {"code": 415, "msg": "unsupported content type"},
#             415,
#             {"Accept": ','.join(ACCEPTED_MIMETYPES)},
#         )

#     charset = request.mimetype_params.get("charset", "utf-8")
#     if charset != "utf-8":
#         name = name.encode(charset).decode()

#     if len(name) == 0:
#         return ({"code": 400, "msg": "missing token name"}, 400)
#     else:
#         token = generate_token()
#         user_id = request.authorization["user_id"]
#         user_ip = request.remote_addr

#         db = get_db()
#         result = db.execute("SELECT id FROM user WHERE name = ?", (name,)).fetchone()
#         if result:
#             return ({"code": 409, "msg": "token name already in use"}, 409)
#         else:
#             db.execute(
#                 "INSERT INTO user (name,token,ip,created_by) VALUES (?, ?, ?, ?)",
#                 (
#                     name,
#                     token,
#                     user_ip,
#                     user_id,
#                 ),
#             )
#             db.commit()
#             return {"token": token}


# @v1.route("/echo", methods=["GET", "POST", "DELETE", "PATCH", "PUT"])
# @flask_login.login_required
# def echo_route():
#     if request.mimetype not in ACCEPTED_MIMETYPES:
#         return (
#             {"code": 400, "msg": "missing content type"},
#             400,
#             {"Accept": ','.join(ACCEPTED_MIMETYPES)},
#         )

#     if request.is_json:
#         name = str(request.json.get("name", ""))
#     elif request.mimetype == "application/x-www-form-urlencoded":
#         name = request.form.get("name", default="", type=str)
#     elif request.mimetype == "text/plain":
#         name = request.data.decode().strip()
#     else:
#         return (
#             {"code": 415, "msg": "unsupported content type"},
#             415,
#             {"Accept": "application/json,application/x-www-form-urlencoded,text/plain"},
#         )

#     charset = request.mimetype_params.get("charset", "utf-8")
#     if charset != "utf-8":
#         name = name.encode(charset).decode()

#     attrs = [
#         "path",
#         "full_path",
#         "url",
#         "base_url",
#         "url_root",
#         "authorization",
#         "is_json",
#         "content_encoding",
#         "content_type",
#         "endpoint",
#         "host",
#         "host_url",
#         "method",
#         "origin",
#         "range",
#         "mimetype",
#         "mimetype_params",
#         "referrer",
#         "remote_addr",
#         "scheme",
#         "is_secure",
#         "url_charset",
#     ]
#     d = {}
#     for a in sorted(attrs):
#         d[a] = getattr(request, a)
#     d["user_agent"] = str(request.user_agent)
#     d["name"] = name
#     return d
