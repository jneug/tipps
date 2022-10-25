import os
from pathlib import Path

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY="dev",
        # SERVER_NAME='tipp.ngb.schule',
        # BASEURL=None,
        REMEMBER_USER=True,
        DATABASE=os.path.join(app.instance_path, "tipps.db"),
        DATA_PATH=app.instance_path + "/data",
        PAGEPATH=app.instance_path + "/pages",
        QRPATH=app.instance_path + "/qrcodes",
        RAWPATH=app.instance_path + "/raw",
        MARKDOWN={
            "extensions": [
                "attr_list",
                "def_list",
                "admonition",
                "tables",
                # "footnotes",
                # "md_in_html",
                "codehilite",
                "fenced_code",
                # "smarty",
                # "toc",
                # "meta",
                # "fenced_code",
                # "pymdownx.superfences",
                # {
                #     "name": "pymdownx.highlight",
                #     "anchor_linenums": True,
                # },
                # "pymdownx.inlinehilite",
                {
                    "name": 'pymdownx.arithmatex',
                    "generic": True
                },
                "pymdownx.caret",
                "pymdownx.smartsymbols",
                {
                    "name": "pymdownx.betterem",
                    "smart_enable": "all",
                },
                {
                    "name": "pymdownx.emoji",
                    "emoji_index": "!!python/name:materialx.emoji.twemoji",
                    "emoji_generator": "!!python/name:materialx.emoji.to_svg",
                },
                # "pymdownx.snippets",
                # "pymdownx.details",
            ]
        },
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    folders = [
        app.instance_path,
        app.config["DATA_PATH"],
        # app.config["PAGEPATH"],
        # app.config["RAWPATH"],
        # app.config["QRPATH"],
    ]
    for f in folders:
        try:
            os.makedirs(f)
        except OSError:
            pass

    from . import db

    db.init_app(app)

    # create db on first start
    if not Path(app.config["DATABASE"]).exists():
        with app.app_context():
            db.init_db()

    # initialize login manager
    from . import auth

    with app.app_context():
        auth.get_login_manager()

    from .cli import register_commands
    register_commands(app)

    from . import api
    app.register_blueprint(api.v1)

    from . import web
    app.register_blueprint(web.web)

    app.jinja_env.add_extension('jinja2_ansible_filters.AnsibleCoreFiltersExtension')

    return app
