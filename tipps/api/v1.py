from flask import Blueprint, request, current_app, g

from pathlib import Path
from functools import wraps

from tipps.db import get_db
from tipps.util import *


def restricted(func):
	@wraps(func)
	def authenticate(*args, **kwargs):
		if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Bearer'):
			token = request.headers['Authorization'][7:].strip()

			db = get_db()
			user_id = db.execute('SELECT id FROM user WHERE token = ?', (token,)).fetchone()
			if user_id:
				request.authorization = {'type': 'bearer', 'user_id': user_id['id'], 'token': token}
				return func(*args, **kwargs)
		return ({'code': 401, 'msg': 'authentication failed'}, 401)
	return authenticate


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

	# filters
	filters = {}

	template = request.args.get('template', default=None)
	if template:
		filters['tipp.template'] = template
	if token:
		filters['user.token'] = token

	if len(filters) > 0:
		where = 'WHERE ' + ', '.join([f'{k} = ?' for k in filters.keys()])
	else:
		where = ''

	db = get_db()
	result = db.execute(f'SELECT tipp.id,tipp.created,tipp.template FROM tipp INNER JOIN user ON user.id = tipp.user_id {where} ORDER BY {sort} LIMIT {limit} OFFSET {offset}', tuple(filters.values())).fetchall()

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

@v1.route('/templates')
def list_templates():
	# list template files in templates folder
	# perhaps makes sense to move the tipp templates to another folder
	# e.g. assets/templates
	templates = get_templates()
	return {'templates': sorted(templates)}

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

@v1.route('/tipps/<string:id>', methods=['PUT'])
def tipp_update(id):
	if request.mimetype == '':
		return ({'code': 400, 'msg': 'missing content type'}, 400, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	if request.is_json:
		content = str(request.json.get('content', ''))
		template = str(request.json.get('template', 'default'))
	elif request.mimetype == 'application/x-www-form-urlencoded':
		content = request.form.get('content', default='', type=str)
		template = request.form.get('template', default='default', type=str)
	elif request.mimetype == 'text/plain':
		content = request.data.decode().strip()
		template = 'default'
	else:
		return ({'code': 415, 'msg': 'unsupported content type'}, 415, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	charset = request.mimetype_params.get('charset', 'utf-8')
	if charset != 'utf-8':
		content = content.encode(charset).decode()
		template = template.encode(charset).decode()

	if len(content.strip()) == 0:
		return ({'code': 400, 'msg': 'content may not be empty'}, 400)

	timestamp = update_tipp(id, content, template=template)

	db = get_db()
	db.execute('UPDATE tipp SET compiled = ?, template = ? WHERE id = ?', (timestamp, template, id,))
	db.commit()

	return ({
		'id': id,
		'compiled': timestamp,
		'template': template
	}, 200)

@v1.route('/tipps/<string:id>', methods=['PATCH'])
def tipp_compile(id):
	db = get_db()
	result = db.execute('SELECT template FROM tipp WHERE id = ?', (id,)).fetchone()
	if result:
		# TODO: allow form-date / plaintext here?
		template = str(request.json.get('template', result['template']))
		timestamp = compile_tipp(id, template=template)
		db.execute('UPDATE tipp SET compiled = ?, template = ? WHERE id = ?', (timestamp, template, id,))
		db.commit()
		return {
			'id': id,
			'compiled': timestamp,
			'template': template
		}
	else:
		return ({'code': 400, 'msg': 'unknown id'}, 400)

@v1.route('/tipps/<string:id>', methods=['DELETE'])
@restricted
def tipp_delete(id):
	db = get_db()
	result = db.execute('SELECT user_id FROM tipp WHERE id = ?', (id,)).fetchone()
	if not result:
		return({'code': 404, 'msg': f'unknown id'}, 404)
	if result['user_id'] != request.authorization['user_id']:
		return({'code': 403, 'msg': f'tipp owned by other token'}, 403)
	db.execute('DELETE FROM tipp WHERE id = ? AND user_id = ?', (id, request.authorization['user_id'],))
	db.commit()
	return ('', 204)

@v1.route('/tipps', methods=['POST'])
@restricted
def tipp_create():
	if request.mimetype == '':
		return ({'code': 400, 'msg': 'missing content type'}, 400, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	if request.is_json:
		content = str(request.json.get('content', ''))
		template = str(request.json.get('template', 'default'))
	elif request.mimetype == 'application/x-www-form-urlencoded':
		content = request.form.get('content', default='', type=str)
		template = request.form.get('template', default='default', type=str)
	elif request.mimetype == 'text/plain':
		content = request.data.decode().strip()
		template = 'default'
	else:
		return ({'code': 415, 'msg': 'unsupported content type'}, 415, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	charset = request.mimetype_params.get('charset', 'utf-8')
	if charset != 'utf-8':
		content = content.encode(charset).decode()
		template = template.encode(charset).decode()

	if len(content.strip()) == 0:
		return ({'code': 400, 'msg': 'content may not be empty'}, 400)

	id = create_tipp(content, template=template)

	db = get_db()
	db.execute('INSERT INTO tipp (id,user_id,template) VALUES (?, ?, ?)', (id, request.authorization['user_id'], template,))
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
@restricted
def token_create():
	if request.mimetype == '':
		return ({'code': 400, 'msg': 'missing content type'}, 400, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	if request.is_json:
		name = str(request.json.get('name', ''))
	elif request.mimetype == 'application/x-www-form-urlencoded':
		name = request.form.get('name', default='', type=str)
	elif request.mimetype == 'text/plain':
		name = request.data.decode().strip()
	else:
		return ({'code': 415, 'msg': 'unsupported content type'}, 415, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	charset = request.mimetype_params.get('charset', 'utf-8')
	if charset != 'utf-8':
		name = name.encode(charset).decode()

	if len(name) == 0:
		return ({'code': 400, 'msg': 'missing token name'}, 400)
	else:
		token = generate_token()
		user_id = request.authorization['user_id']
		user_ip = request.remote_addr

		db = get_db()
		result = db.execute('SELECT id FROM user WHERE name = ?', (name,)).fetchone()
		if result:
			return ({'code': 409, 'msg': 'token name already in use'}, 409)
		else:
			db.execute('INSERT INTO user (name,token,ip,created_by) VALUES (?, ?, ?, ?)', (name, token, user_ip, user_id,))
			db.commit()
			return {'token': token}

@v1.route('/echo', methods=['GET', 'POST', 'DELETE', 'PATCH', 'PUT'])
@restricted
def echo_route():
	if request.mimetype == '':
		return ({'code': 400, 'msg': 'missing content type'}, 400, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	if request.is_json:
		name = str(request.json.get('name', ''))
	elif request.mimetype == 'application/x-www-form-urlencoded':
		name = request.form.get('name', default='', type=str)
	elif request.mimetype == 'text/plain':
		name = request.data.decode().strip()
	else:
		return ({'code': 415, 'msg': 'unsupported content type'}, 415, {'Accept': 'application/json,application/x-www-form-urlencoded,text/plain'})

	charset = request.mimetype_params.get('charset', 'utf-8')
	if charset != 'utf-8':
		name = name.encode(charset).decode()

	attrs = ['path', 'full_path', 'url', 'base_url',
		'url_root', 'authorization', 'is_json', 'content_encoding', 'content_type',
		'endpoint', 'host', 'host_url', 'method', 'origin', 'range', 'mimetype', 'mimetype_params',
		'referrer', 'remote_addr', 'scheme', 'is_secure', 'url_charset']
	d = {}
	for a in sorted(attrs):
		d[a] = getattr(request, a)
	d['user_agent'] = str(request.user_agent)
	d['name'] = name
	return d
