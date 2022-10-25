import markdown

from flask import current_app, g


def get_parser() -> markdown.Markdown:
    if "mdown" not in g:
        _config: dict = dict(extensions=list(), extension_config=dict())
        if "MARKDOWN" in current_app.config:
            if "extensions" in current_app.config["MARKDOWN"]:
                for ext in current_app.config["MARKDOWN"]["extensions"]:
                    if isinstance(ext, str):
                        _config["extensions"].append(ext)
                    else:
                        if "name" in ext:
                            _name = ext["name"]
                            del ext["name"]

                            _config["extensions"].append(_name)
                            _config["extension_config"][_name] = {**ext}
                del current_app.config["MARKDOWN"]["extensions"]
            _config.update(current_app.config["MARKDOWN"])

        g.mdown = markdown.Markdown(**_config)
    return g.mdown
