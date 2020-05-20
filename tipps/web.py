from flask import Blueprint, request, current_app, abort, g, send_file

from pathlib import Path

from tipps.db import get_db
from tipps.util import *

web = Blueprint('web', __name__)

@web.route('/')
def start():
	return 'Tipps'

@web.route('/<string:id>')
def show_tipp(id):
	page_path = Path(current_app.config['PAGEPATH']) / f'{id}.html'
	if page_path.is_file():
		return send_file(page_path, mimetype='text/html')
	else:
		abort(404)

@web.route('/qr/<string:id>')
def show_qr(id):
	qr_path = Path(current_app.config['QRPATH']) / f'{id}.png'
	if qr_path.is_file():
		return send_file(qr_path, mimetype='image/png')
	else:
		abort(404)
