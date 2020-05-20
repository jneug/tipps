import sqlite3
import click
import os
from pathlib import Path

from flask import current_app, g
from flask.cli import with_appcontext

from tipps.db import init_db, get_db
from tipps.util import compile_tipp

def register_commands(app):
	app.cli.add_command(init_db_command)
	app.cli.add_command(recompile_command)
	app.cli.add_command(maintenance_command)
	app.cli.add_command(cleanup_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

@click.command('recompile')
@with_appcontext
def recompile_command():
	click.echo('Recompiling all known tipps. This might take a while!')
	db = get_db()
	result = db.execute('SELECT id,template FROM tipp').fetchall()
	for tipp in result:
		compile_tipp(tipp['id'], template=tipp['template'])
		click.echo(f'Compiled tipp {tipp["id"]}.')
	click.echo('Done compiling.')

@click.command('maintenance')
@with_appcontext
def maintenance_command():
	db = get_db()

	raw_path = Path(current_app.config['RAWPATH'])
	for raw in raw_path.glob('*.md'):
		result = db.execute('SELECT template FROM tipp WHERE id = ?', (raw.stem,)).fetchone()
		if not result:
			db.execute('INSERT INTO tipp (id,user_id) VALUES (?, 1)', (raw.stem,))
			result = {'template':'default'}
			click.echo(f'Added tipp {raw.stem} to database.')
		page_path = Path(current_app.config['PAGEPATH']) / f'{id}.html'
		if not page_path.is_file():
			compile_tipp(id, template=result['template'])
			click.echo(f'Compiled tipp {raw.stem}.')
	db.commit()
	click.echo('Done!')

@click.command('cleanup')
@with_appcontext
def cleanup_command():
	click.echo('Cleaning up old tipps.')
