import os
from pathlib import Path

from flask import Flask


def create_app(test_config=None):
	# create and configure the app
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='dev',
		SERVER_NAME='0.0.0.0:5000',
		DATABASE=os.path.join(app.instance_path, 'tipps.db'),
		PAGEPATH=os.path.join(app.instance_path,'/pages'),
		QRPATH=os.path.join(app.instance_path,'/qrcodes'),
		RAWPATH=os.path.join(app.instance_path,'/raw'),
		BASEURL=None,
		MARKDOWN={'extensions': ['tables'] }
	)

	if test_config is None:
		# load the instance config, if it exists, when not testing
		app.config.from_pyfile('config.py', silent=True)
	else:
		# load the test config if passed in
		app.config.from_mapping(test_config)

	# ensure the instance folder exists
	folders = [
		app.instance_path,
		app.config['PAGEPATH'],
		app.config['RAWPATH'],
		app.config['QRPATH'] ]
	for f in folders:
		try:
			os.makedirs(f)
		except OSError:
			pass

	from . import db
	db.init_app(app)
	# create db on first start
	if not Path(app.config['DATABASE']).exists():
		with app.app_context():
			db.init_db()

	from .cli import register_commands
	register_commands(app)

	from . import api
	app.register_blueprint(api.v1)

	from . import web
	app.register_blueprint(web.web)

	return app

