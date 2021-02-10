from flask import Blueprint, request, current_app, abort, g, send_file, render_template, redirect, url_for

from pathlib import Path

from tipps.db import get_db
from tipps.util import *

web = Blueprint('web', __name__)

@web.route('/', methods=['GET', 'POST'])
def start():
	if request.method == 'POST':
		code = request.form.get('code', default=None, type=str)
		if code:
			return redirect(url_for('web.show_tipp', id=id), 303)
		return render_template('index.html', error='Zu deinem Code konnten wir leider keinen Tipp finden. Hast du dich vielleicht vertippt? Versuch es ruhig noch einmal.')
	else:
		return render_template('index.html')

@web.route('/create', methods=['GET', 'POST'])
def create():
	if request.method == 'POST':
		content = request.form.get('content', default='', type=str)
		token = request.form.get('token', default='', type=str)
		template = request.form.get('template', default='default', type=str)

		if len(content.strip()) == 0 or len(token.strip()) == 0:
			return render_template('input.html', content=content, token=token, template=template, templates=get_templates(), error="Der Inhalt darf nicht leer sein.")

		db = get_db()
		user_id = db.execute('SELECT id FROM user WHERE token = ?', (token,)).fetchone()
		if not user_id:
			return render_template('input.html', content=content, token=token, template=template, templates=get_templates(), error="Kein gültiges Token.")

		id = create_tipp(content, template=template)

		db.execute('INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)', (id, user_id['id'], template,))
		db.commit()

		return redirect(url_for('web.show_tipp', id=id), 303)
	else:
		return render_template('input.html', templates=get_templates())


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
