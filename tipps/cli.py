import os
import sqlite3
from datetime import datetime

from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext, AppGroup
from werkzeug.security import generate_password_hash

from .db import get_db, init_db
from .util import compile_tipp, mtime, ctime, generate_token, generate_password
from .model import Tipp, Template, DEFAULT_TEMPLATE


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(user_group)
    app.cli.add_command(migrate_command)
    app.cli.add_command(recompile_command)
    app.cli.add_command(maintenance_command)
    app.cli.add_command(delete_command)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


user_group = AppGroup("user")


@user_group.command("list")
@with_appcontext
def user_list_command():
    db = get_db()
    result = db.execute("SELECT id,name FROM user ORDER BY id ASC").fetchall()
    if result:
        click.secho("  ID  Name", fg="bright_yellow")
        for row in result:
            click.secho(f"{row['id']:> 4}  {row['name']}", fg="yellow")


@user_group.command("create")
@click.argument("name")
@click.option(
    "-p", "--password",
    help="Password for the new user. Without this option a random password is created and printed to the terminal."
)
@with_appcontext
def user_create_command(name: str, password: str = None):
    """Create a new user for this Tipps instance."""
    db = get_db()

    # check username
    result = db.execute("SELECT id FROM user WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
    if result:
        click.secho(f"Username {name} already exists. Choose another.", fg="bright_red")
        return

    # create and hash password
    password = password or generate_password()
    password_hash = generate_password_hash(password)

    # create api-token
    token = generate_token()

    db.execute(
        "INSERT INTO user (name, password, token) VALUES (?, ?, ?)",
        (name, password_hash, token)
    )
    db.commit()

    result = db.execute(
        "SELECT id FROM user WHERE name = ?",
        (name, )
    ).fetchone()
    id = result['id']

    click.secho(f"Created new user with id {id}:", fg="bright_green")
    click.secho(f"  Name: {name}", fg="yellow")
    click.secho(f"  Password: {password}", fg="yellow")
    click.secho(f"  API-Token: {token}", fg="yellow")


@click.command("migrate")
@with_appcontext
def migrate_command():
    """Migrate tipp files to new Tipps version."""
    click.secho("Migrating all known tipps. This might take a while!", fg="cyan")

    click.secho("Old paths", fg="bright_yellow")
    click.secho(f"-> RAWPATH: {current_app.config['RAWPATH']}", fg="yellow")
    click.secho(f"-> PAGEPATH: {current_app.config['PAGEPATH']}", fg="yellow")
    click.secho(f"-> QRPATH: {current_app.config['QRPATH']}", fg="yellow")
    click.secho("Old path", fg="bright_yellow")
    click.secho(f"-> DATA_PATH: {current_app.config['DATA_PATH']}", fg="yellow")

    def move(source: Path, target: Path) -> bool:
        if source.exists() and not target.exists():
            source.replace(target)
            return True
        return False

    db = get_db()
    result = db.execute("SELECT * FROM tipp").fetchall()
    with click.progressbar(
        result, label="Migrating tipps", item_show_func=lambda r: r["id"] if r else None
    ) as tipps:
        for tipp in tipps:
            t = Tipp(**tipp)

            t.root.mkdir(parents=True, exist_ok=True)
            move(Path(current_app.config["RAWPATH"]) / f"{t.id}.md", t.raw_path)
            move(Path(current_app.config["PAGEPATH"]) / f"{t.id}.html", t.page_path)
            move(Path(current_app.config["QRPATH"]) / f"{t.id}.png", t.qr_path)

    # raw_path = Path(current_app.config["RAWPATH"])
    # for file in raw_path.iterdir():
    #     if file.suffix == '.md':
    #         t = Tipp(id=file.stem)

    #         t.root.mkdir(parents=True, exist_ok=True)
    #         move(Path(current_app.config["RAWPATH"]) / f"{t.id}.md", t.raw_path)
    #         move(Path(current_app.config["PAGEPATH"]) / f"{t.id}.html", t.page_path)
    #         move(Path(current_app.config["QRPATH"]) / f"{t.id}.png", t.qr_path)

    click.secho("Migration done.", fg="bright_green")


@click.command("recompile")
@click.option("-t", "--template", help="Specify a template to recompile.")
@click.option(
    "-s",
    "--smart",
    is_flag=True,
    help="Only recompile tipps whose raw file is newer than their page file.",
)
@with_appcontext
def recompile_command(template: str = None, smart: bool = False):
    """Recompiles tipps from their raw files."""
    if template:
        click.secho(
            f"Recompiling all known tipps for template {template}. This might take a while!",
            fg="cyan",
        )
    else:
        click.secho("Recompiling all known tipps. This might take a while!", fg="cyan")

    db = get_db()
    if template:
        result = db.execute(
            "SELECT id, template FROM tipp WHERE template = ?", (template,)
        ).fetchall()  # type: list
    else:
        result = db.execute("SELECT id, template FROM tipp").fetchall()

    i = 0
    count = len(result)
    with click.progressbar(
        result,
        label="Recompiling tipps",
        item_show_func=lambda r: r["id"] if r else None,
    ) as tipps:
        for _tipp in tipps:
            tipp = Tipp(**_tipp)

            if smart:
                if (
                    (mt1 := mtime(tipp.raw_path))
                    and (mt2 := mtime(tipp.page_path))
                    and mt1 > mt2
                ):
                    tipp.compile()
                    i += 1
            else:
                tipp.compile()
                i += 1

    click.secho(f"Done: {i} of {count} tipps recompiled.", fg="bright_green")


@click.command("maintenance")
@click.option(
    "-a",
    "--add",
    is_flag=True,
    help="Adds orphaned files to the database. Needs the --user options to be present. Overwrites the remove option.",
)
@click.option(
    "-u", "--user", type=int, help="Specifies a user id orphaned files are added for."
)
@click.option("-rm", "--remove", is_flag=True, help="Removes orphaned files from disk.")
@with_appcontext
def maintenance_command(add: bool = False, remove: bool = False, user: int = None):
    """Looks for orphaned files in the data path and either deletes them or adds them to the database. Also removes database entries without files from the database."""
    db = get_db()

    tipps_result = db.execute("SELECT id FROM tipp").fetchall()

    # check options
    if add and not user:
        click.secho("Specify a user id for the --add option.", fg="bright_red")
        return

    click.secho("Looking for orphaned files. This might take a while!", fg="cyan")

    _changed = []
    data_path = Path(current_app.config["DATA_PATH"])
    with click.progressbar(
        data_path.glob("**/*.md"),
        label="Checking orphaned files",
        item_show_func=lambda r: r.stem if r else None,
    ) as files:
        for raw in files:
            id = raw.stem
            result = db.execute("SELECT template FROM tipp WHERE id = ?", (id,)).fetchone()

            if not result and add:
                db.execute(
                    "INSERT INTO tipp (id,user_id,created,template) VALUES (?, ?, ?, ?)",
                    (id, user, ctime(raw), DEFAULT_TEMPLATE.name),
                )

                tipp = Tipp(id, template=DEFAULT_TEMPLATE)
                if not tipp.page_path.is_file():
                    tipp.compile()

                _changed.append(id)
            elif result and remove:
                tipp = Tipp(id, template=result["template"])
                tipp.delete()
                _changed.append(id)

    # commit changes
    if add:
        db.commit()

    click.secho("Done. Added/Removed tipps: " + (','.join(_changed) if _changed else "None"), fg="bright_green")

    if tipps_result:
        click.secho("Looking for orphaned database entries.", fg="cyan")

        for row in tipps_result:
            tipp = Tipp(**row)
            if not tipp.exists():
                db.execute("DELETE FROM tipp WHERE id = ?", (tipp.id,))

        db.commit()
        click.secho("Done.", fg="bright_green")


@click.command("delete")
@click.option(
    "--id", type=int,
    help="Specifies a tipp id (or comma separated list of ids) to delete."
)
@click.option(
    '--user', type=int,
    help="Specifies a user id to delete all tipps from."
)
@click.option(
    '--before', type=click.DateTime(),
    help="Specifies a date and deletes all tipps created before that date."
)
@click.option(
    '--mtime', is_flag=True,
    help="Makes date based options use the modification time instead of creation time."
)
@with_appcontext
def delete_command(id):
    tipp = Tipp(id)
    if tipp.exists():
        tipp.delete()

    db = get_db()
    db.execute("DELETE FROM tipp WHERE id = ?", (id,))
    db.commit()

    click.secho(f"Tipp {id} deleted.", fg="bright_green")
