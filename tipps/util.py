import os
import re
import string
from datetime import datetime
from pathlib import Path
from random import choices

import markdown
import qrcode
from flask import Markup, current_app, render_template, url_for


def generate_id():
    alphabet = string.ascii_lowercase + string.digits
    return "-".join(["".join(choices(alphabet, k=4)) for i in range(3)])


def generate_token():
    alphabet = string.ascii_letters
    return "".join(choices(alphabet, k=32))


def get_templates():
    return ["default", "math", "video", "image", "code", "mermaid", "quote", "scratch"]


def get_template_name(name):
    tpl_path = Path(current_app.root_path) / "templates" / name
    if tpl_path.is_dir():
        tpl_path = tpl_path / "default.html"
        name = f"{name}/default"
    else:
        tpl_path = Path(current_app.root_path) / "templates" / f"{name}.html"

    if tpl_path.is_file():
        return f"{name}.html"
    else:
        return "default.html"


def get_tipp_url(id):
    if "BASE_URL" in current_app.config:
        return f'{current_app.config["BASE_URL"]}/{id}'
    else:
        return url_for("web.show_tipp", id=id, _external=True)
    # return f'{current_app.config["BASEURL"]}/{id}'


def get_qr_url(id):
    if "BASE_URL" in current_app.config:
        return f'{current_app.config["BASE_URL"]}/qr/{id}'
    else:
        return url_for("web.show_qr", id=id, _external=True)
    # return f'{current_app.config["BASEURL"]}/qr/{id}'


def get_tipp_content(id):
    """
    Read the tipps content from its raw file.
    """
    raw_path = Path(current_app.config["RAWPATH"]) / f"{id}.md"
    if raw_path.is_file():
        return raw_path.read_text()
    else:
        return ""


def get_tipp_title(id):
    """
    Read the tipps first heading from the raw content. Returns
    the id if no heading exists.
    """
    raw_path = Path(current_app.config["RAWPATH"]) / f"{id}.md"
    if raw_path.is_file():
        with open(raw_path, "rt") as fh:
            if m := re.search(r"#+\s+(.+)", fh.readline()):
                return m.group(1)
    else:
        return id


def get_tipp_excerpt(id, length=50):
    """
    Reads an excerpt of the tipp from its raw content.
    """
    raw_path = Path(current_app.config["RAWPATH"]) / f"{id}.md"
    if raw_path.is_file():
        with open(raw_path, "rt") as fh:
            return fh.read(length) + "..."
    else:
        return ""


def create_tipp(body, id=None, template="default"):
    id = id if id else generate_id()

    raw_path = Path(current_app.config["RAWPATH"]) / f"{id}.md"
    raw_path.write_text(body)

    qr_img = qrcode.make(get_tipp_url(id))
    qr_path = Path(current_app.config["QRPATH"]) / f"{id}.png"
    qr_img.save(qr_path)

    compile_tipp(id, template=template, body=body)
    return id


def update_tipp(id, body, template=None):
    raw_path = Path(current_app.config["RAWPATH"]) / f"{id}.md"
    raw_path.write_text(body)

    return compile_tipp(id, template=template, body=body)


def compile_tipp(id, template="default", body=None):
    if not body:
        raw_path = Path(current_app.config["RAWPATH"]) / f"{id}.md"
        if raw_path.is_file():
            body = raw_path.read_text()

    if body:
        html_content = markdown.markdown(
            body, extensions=current_app.config["MARKDOWN"]["extensions"]
        )
        tpl_vars = {
            "baseurl": current_app.config["SERVER_NAME"],
            "url": get_tipp_url(id),
            "qrurl": get_qr_url(id),
            "id": id,
            "content": Markup(html_content),
        }
        content = render_template(get_template_name(template), **tpl_vars)

        page_path = Path(current_app.config["PAGEPATH"]) / f"{id}.html"
        page_path.write_text(content)

        return datetime.fromtimestamp(os.path.getmtime(str(page_path)))


def delete_tipp(id):
    """Removes a tipp from the caches."""
    paths = [
        Path(current_app.config["RAWPATH"]) / f"{id}.md",
        Path(current_app.config["PAGEPATH"]) / f"{id}.html",
        Path(current_app.config["QRPATH"]) / f"{id}.png",
    ]
    for p in paths:
        if p.is_file():
            p.unlink()
