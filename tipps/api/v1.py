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

@v1.route('/tipps')
@v1.route('/tokens/<string:token>/tipps')
def list_tipps(token=None):
	details = request.args.get('details', default=False, type=bool)

	sort = request.args.get('sort', default='created_desc', type=str).lower().split('_')
	if sort[0] == 'rand':
		sort[0] = 'RANDOM()'
	elif sort[0] not in ['created','compiled','id']:
		sort[0] = 'tipp.created'
	else:
		sort[0] = f'tipp.{sort[0]}'
	if len(sort) < 2:
		sort.append('asc')
	elif sort[1] not in ['asc', 'desc']:
		sort[1] = 'asc'
	sort = f'{sort[0]} {sort[1].upper()}'

	limit = request.args.get('limit', default=20, type=int)
	offset = request.args.get('offset', default=0, type=int)

	db = get_db()
	if token is None:
		result = db.execute(f'SELECT id,created,template FROM tipp ORDER BY {sort} LIMIT {limit} OFFSET {offset}').fetchall()
	else:
		result = db.execute(f'SELECT tipp.id,tipp.created,tipp.template FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = ? ORDER BY {sort} LIMIT {limit} OFFSET {offset}', (token,)).fetchall()

	tipps = []
	if not details:
		for row in result:
			tipps.append(row['id'])
	else:
		for row in result:
			tipps.append({
				'id': row['id'],
				'url': get_tipp_url(row["id"]),
				'qrurl': get_qr_url(row["id"]),
				'created': row['created'],
				'template': row['template']
			})
	return {'tipps': tipps}

@v1.route('/tipps/<string:id>')
def tipp_details(id):
	db = get_db()

	result = db.execute('SELECT * FROM tipp WHERE id = ?', (id,)).fetchone()
	if result:
		tipp = {
			'id': id,
			'created': result['created'],
			'compiled': result['compiled'],
			'template': result['template'],
			'url': get_tipp_url(id),
			'qrurl': get_qr_url(id),
			'content': ''
		}

		raw_path = Path(current_app.config['RAWPATH']) / f'{id}.md'
		if raw_path.is_file():
			tipp['content'] = raw_path.read_text()

		return tipp
	else:
		return ({'error': 404, 'msg': f'unknown id'}, 404)

@v1.route('/tipps/<string:id>', methods=['PATCH'])
def tipp_compile(id):
	template = request.args.get('template', default=None, type=str)

	db = get_db()
	result = db.execute('SELECT template FROM tipp WHERE id = ?', (id,)).fetchone()
	if result:
		if not template:
			template = result['template']
		timestamp = compile_tipp(id, template=template)
		db.execute('UPDATE tipp SET compiled = ? WHERE id = ?', (timestamp, id,))
		db.commit()
		return {
			'id': id,
			'compiled': timestamp
		}
	else:
		return ({'code': 400, 'msg': 'unknown id'}, 400)

@v1.route('/tipps/<string:id>', methods=['DELETE'])
def tipp_delete(id):
	if not authenticate():
		return ({'code': 401, 'msg': 'authentication failed'}, 401)
	db = get_db()
	result = db.execute('SELECT user_id FROM tipp WHERE id = ?', (id,)).fetchone()
	if not result:
		return({'code': 404, 'msg': f'unknown id'}, 404)
	if result['user_id'] != g.auth['user_id']:
		return({'code': 403, 'msg': f'tipp owned by other token'}, 403)
	db.execute('DELETE FROM tipp WHERE id = ? AND user_id = ?', (id, g.auth['user_id'],))
	db.commit()
	return ('', 204)

@v1.route('/tipps', methods=['POST'])
def tipp_create():
	if not authenticate():
		return ({'code': 401, 'msg': 'authentication failed'}, 401)

	#template = request.args.get('template', default='default', type=str)

	#content = request.data.decode().strip()
	#if len(content) == 0:
	#	content = request.form.get('content', default='').strip()
	#if len(content) == 0:
	#	return ({'code': 400, 'msg': 'body may not be empty'}, 400)

	if 'content' not in request.json:
		return ({'code': 400, 'msg': 'content may not be empty'}, 400)
	content = str(request.json['content'])

	template = 'default'
	if 'template' in request.json:
		template = str(request.json['template'])

	id = create_tipp(content, template=template)

	db = get_db()
	db.execute('INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)', (id, g.auth['user_id'], template,))
	db.commit()

	return ({
		'id': id,
		'created': datetime.now(),
		'compiled': datetime.now(),
		'template': template,
		'url': get_tipp_url(id),
		'qrurl': get_qr_url(id),
		'content': content
	}, 201)

@v1.route('/tokens', methods=['POST'])
def token_create():
	if not authenticate():
		return ({'code': 401, 'msg': 'authentication failed'}, 401)

	data = request.json
	if 'name' not in data or len(data['name']) == 0:
		return ({'code': 400, 'msg': 'missing token name'}, 400)
	else:
		token = generate_token()
		user_id = g.auth['user_id']
		name = data['name']

		db = get_db()
		result = db.execute('SELECT id FROM user WHERE name = ?', (name,)).fetchone()
		if result:
			return ({'code': 409, 'msg': 'token name already in use'}, 409)
		else:
			db.execute('INSERT INTO user (name,token,ip,created_by) VALUES (?, ?, ?, ?)', (name, token, '0.0.0.0', user_id,))
			db.commit()
			return {'token': token}
