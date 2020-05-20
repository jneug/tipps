from flask import Blueprint, request, current_app, g

from pathlib import Path

from tipps.db import get_db
from tipps.util import *

def authenticate():
	if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Bearer'):
		token = request.headers['Authorization'][7:].strip()

		db = get_db()
		user_id = db.execute('SELECT id FROM user WHERE token = ?', (token,)).fetchone()
		if user_id:
			g.auth = {'user_id': user_id['id'], 'token': token}
			return True
	return False


v1 = Blueprint('api/v1', __name__, url_prefix='/api/v1')

@v1.route('/tipp/list')
@v1.route('/tipp/list/<string:token>')
def list_tipps(token=None):
	details = bool(request.args['details']) if 'details' in request.args else False

	db = get_db()
	if token is None:
		result = db.execute('SELECT id,created,template FROM tipp').fetchall()
	else:
		result = db.execute('SELECT tipp.id,tipp.created,tipp.template FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = ?', (token,)).fetchall()

	tipps = []
	for row in result:
		tipp = {'id': row['id']}
		if details:
			tipp['url'] = get_tipp_url(row["id"])
			tipp['qrurl'] = get_qr_url(row["id"])
		tipps.append(tipp)
	return {'tipps': tipps}

@v1.route('/tipp/<string:id>')
def tipp_details(id):
	include_raw = bool(request.args['raw']) if 'raw' in request.args else False
	include_html = bool(request.args['html']) if 'html' in request.args else False

	db = get_db()

	result = db.execute('SELECT * FROM tipp WHERE id = ?', (id,)).fetchone()
	if result:
		tipp = {
			'id': id,
			'created': result['created'],
			'template': result['template'],
			'url': get_tipp_url(id),
			'qrurl': get_qr_url(id),
		}

		if include_raw:
			raw_path = Path(current_app.config['RAWPATH']) / f'{id}.md'
			if raw_path.is_file():
				tipp['body'] = raw_path.read_text()
		if include_html:
			page_path = Path(current_app.config['PAGEPATH']) / f'{id}.html'
			if page_path.is_file():
				tipp['html'] = page_path.read_text()

		return tipp
	else:
		return ({'error': 404, 'msg': f'no tipp with id {id} found'}, 404)

@v1.route('/tipp/compile/<string:id>')
def tipp_compile(id):
	template = request.args['template'] if 'template' in request.args else None

	db = get_db()
	result = db.execute('SELECT template FROM tipp WHERE id = ?', (id,)).fetchone()
	if result:
		if not template:
			template = result['template']
		compile_tipp(id, template=template)
		return {
			'id': id,
			'url': get_tipp_url(id),
			'qrurl': get_qr_url(id),
		}
	else:
		return ({'code': 400, 'msg': 'Unknown id!'}, 400)

@v1.route('/tipp/create', methods=['POST'])
def tipp_create():
	if not authenticate():
		return ({'code': 401, 'msg': 'Authentication failed!'}, 401)

	template = request.args['template'] if 'template' in request.args else 'default'

	body = request.data.decode().strip()
	if len(body) == 0:
		return ({'code': 400, 'msg': 'Body must not be empty!'}, 400)

	id = create_tipp(body, template=template)

	db = get_db()
	db.execute('INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)', (id, g.auth['user_id'], template))
	db.commit()

	return {
		'id': id,
		'url': get_tipp_url(id),
		'qrurl': get_qr_url(id),
	}

@v1.route('/token/create', methods=['POST'])
def token_create():
	if not authenticate():
		return ({'code': 401, 'msg': 'Authentication failed!'}, 401)

	data = request.json
	if 'name' not in data or len(data['name']) == 0:
		return ({'code': 400, 'msg': 'Provide a name for the new token: {"name": "..."}'}, 400)
	else:
		token = generate_token()
		user_id = g.auth['user_id']
		name = data['name']

		db = get_db()
		result = db.execute('SELECT id FROM user WHERE name = ?', (name,)).fetchone()
		if result:
			return ({'code': 400, 'msg': 'Tokenname already in use!'}, 400)
		else:
			db.execute('INSERT INTO user (name,token,ip,created_by) VALUES (?, ?, ?, ?)', (name, token, '0.0.0.0', user_id,))
			db.commit()
			return {'token': token}
