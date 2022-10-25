import os
import re
import string
from datetime import datetime
from random import choices
from math import ceil

from typing import Generator, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field

import markdown
import qrcode
from flask import Markup, current_app, render_template, url_for, request
from flask_login import UserMixin

from tipps.db import get_db
from . import mdown


TEMPLATES_DIR = "tipp-templates"
TEMPLATES_PATH = Path("templates") / TEMPLATES_DIR


@dataclass
class User(UserMixin):
    id: int
    token: str

    name: Optional[str] = None
    password: str = ""
    is_admin: bool = False
    created: datetime = datetime.now()

    def __post_init__(self):
        self.is_admin = bool(self.is_admin)


@dataclass
class Template:
    name: str

    @staticmethod
    def get_templates() -> Generator["Template", None, None]:
        for child in (Path(current_app.root_path) / TEMPLATES_PATH).iterdir():
            if child.suffix == ".html":
                yield Template(child.stem)

    @staticmethod
    def get_template_names() -> List[str]:
        return [tpl.name for tpl in Template.get_templates()]

    @staticmethod
    def get_template_path() -> Path:
        return Path(current_app.root_path) / TEMPLATES_PATH

    def exists(self):
        return self.path.is_file()

    @property
    def basename(self) -> str:
        return f"{TEMPLATES_DIR}/{self.name}.html"

    @property
    def path(self) -> Path:
        return Template.get_template_path() / f"{self.name}.html"

    def __str__(self):
        return self.name


DEFAULT_TEMPLATE = Template("default")


@dataclass
class Tipp:
    @staticmethod
    def search_root(tipp: str) -> Path:
        return Path()

    @staticmethod
    def generate_id() -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "-".join(["".join(choices(alphabet, k=4)) for i in range(3)])

    id: str = field(default_factory=generate_id)
    user_id: int = -1
    template: Template = DEFAULT_TEMPLATE
    created: datetime = field(default_factory=datetime.now)
    compiled: Optional[datetime] = None
    root: Path = field(default_factory=Path, init=False)

    def __post_init__(self):
        directory = f"{self.id[0:2]}/{self.id[5:7]}/{self.id[10:12]}"
        self.root = Path(current_app.config["DATA_PATH"]) / directory

        if isinstance(self.template, str):
            self.template = Template(self.template)

    def exists(self):
        return self.raw_path.is_file()

    @property
    def title(self) -> str:
        if self.exists():
            with open(self.raw_path, "rt") as fh:
                if m := re.search(r"#+\s+(.+)", fh.readline()):
                    return m.group(1)
        return self.id

    @property
    def raw_content(self):
        if self.exists():
            return self.raw_path.read_text()
        else:
            return ""

    @property
    def page_content(self):
        if self.page_path.is_file():
            return self.page_path.read_text()
        else:
            return ""

    def html_content(self, raw=False):
        if self.page_path.is_file() and not raw:
            return self.page_content
        elif self.raw_path.is_file():
            return mdown.get_parser().convert(self.raw_content)
        else:
            return ""

    def __html__(self):
        return self.html_content()

    @property
    def excerpt(self, length=50, suffix="..."):
        excerpt = ""
        if self.exists():
            with open(self.raw_path, "rt") as fh:
                while _line := fh.readline():
                    if not re.search(r"^#(.+)", _line):
                        excerpt += f"{excerpt}\n{_line}"
                    if len(excerpt) >= length:
                        break

        if len(excerpt) > length:
            return excerpt[: -len(suffix)] + suffix
        else:
            return excerpt

    @property
    def url(self) -> str:
        if "BASE_URL" in current_app.config:
            return f'{current_app.config["BASE_URL"]}/{self.id}'
        else:
            return url_for("web.show_tipp", id=self.id, _external=True)

    @property
    def qr_url(self) -> str:
        if "BASE_URL" in current_app.config:
            return f'{current_app.config["BASE_URL"]}/qr/{self.id}'
        else:
            return url_for("web.show_qr", id=self.id, _external=True)

    @property
    def raw_path(self) -> Path:
        return self.root / f"{self.id}.md"

    @property
    def page_path(self) -> Path:
        return self.root / f"{self.id}.html"

    @property
    def qr_path(self) -> Path:
        return self.root / f"{self.id}.png"

    def save(self, body: str) -> None:
        """Saves the raw content body of the tipp to disk and
        (re-)creates the qr-code."""
        if not self.root.exists():
            self.root.mkdir(parents=True)
        self.raw_path.write_text(body)

        qr_img = qrcode.make(self.url)
        qr_img.save(self.qr_path)

        self.compile()

    def compile(self, body=None) -> None:
        if not body:
            body = self.html_content(raw=True)

        if body:
            tpl_vars = {
                "baseurl": current_app.config["SERVER_NAME"],
                "tipp": self,
                "content": Markup(body),
            }

            content = render_template(self.template.basename, **tpl_vars)
            self.page_path.write_text(content)

            self.compiled = datetime.fromtimestamp(
                os.path.getmtime(str(self.page_path))
            )

    def delete(self):
        paths = [self.raw_path, self.page_path, self.qr_path]
        for p in paths:
            if p.is_file():
                p.unlink()


class Pagination:

    def __init__(self, per_page: int = 50, items: int = -1, last: int = -1, page: int = 0, param: str = 'page', range: int = 2):
        self._per_page = per_page
        self._param = param
        self._range = range

        if last > -1:
            self._last = last
        elif items > -1:
            self._last = ceil(items / self._per_page)
        else:
            raise ValueError("Specify either items or last for pagination objects.")

        self._page = request.args.get(self._param, page, type=int)
        if self._page > self._last:
            self._page = self._last
        if self._page < 1:
            self._page = 1

    @property
    def page(self):
        return self._page

    @property
    def last(self):
        return self._last

    @property
    def first(self):
        return 1

    @property
    def next(self):
        return min(self._page + 1, self._last)

    @property
    def prev(self):
        return max(self._page - 1, self.first)

    @property
    def is_first(self):
        return self._page == self.first

    @property
    def is_last(self):
        return self._page == self._last

    @property
    def per_page(self):
        return self._per_page

    @property
    def first_item(self):
        return (self._page - 1) * self._per_page

    @property
    def last_item(self):
        return (self.next - 1) * self._per_page

    @property
    def offset(self):
        return self.first_item

    def pages(self):
        for p in range(self._last + 1):
            yield p

    def range(self):
        _from = max(self._page - self._range, self.first)
        _to = min(self._page + self._range, self._last)

        for p in range(_from, _to + 1):
            yield p

    @property
    def is_range_start(self):
        return self._page - self._range <= self.first

    @property
    def is_range_end(self):
        return self._page + self._range >= self._last

    def url_for_page(self, page: Optional[int] = None, **kwargs) -> str:
        if request.view_args:
            kwargs.update(request.view_args)
        if page is None:
            page = self.page
        return url_for(request.endpoint or ".", **kwargs, page=page)

    def url_for_next(self, **kwargs):
        return self.url_for_page(page=self.next, **kwargs)

    def url_for_prev(self, **kwargs):
        return self.url_for_page(page=self.prev, **kwargs)
