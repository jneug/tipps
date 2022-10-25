import markdown

from flask import current_app, g


EXTENSIONS = {
    "attr_list": None,
    "def_list": None,
    "admonition": None,
    "tables": None,
    # "footnotes",
    # "md_in_html",
    # "smarty",
    # "toc",
    # "meta",
    "pymdownx.superfences": None,
    # "pymdownx.inlinehilite",
    # "codehilite",
    # "fenced_code",
    "pymdownx.highlight": {
        "anchor_linenums": True,
    },
    'pymdownx.arithmatex': None,
    "pymdownx.caret": None,
    "pymdownx.smartsymbols": None,
    "pymdownx.betterem": {"smart_enable": "all"},
    "pymdownx.emoji": {
        "emoji_index": "python/name:materialx.emoji.twemoji",
        "emoji_generator": "python/name:materialx.emoji.to_svg",
    },
    # "pymdownx.snippets",
    # "pymdownx.details",
}


def get_parser() -> markdown.Markdown:
    _config: dict = dict(extensions=list(), extension_config=dict())
    for name, conf in EXTENSIONS.items():
        _config['extensions'].append(name)
        if conf:
            _config["extension_config"][name] = conf
    return markdown.Markdown(**_config)
