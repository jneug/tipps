from flask import current_app, render_template, Markup, url_for

import string
from random import choices
import markdown
import qrcode
from pathlib import Path

def generate_id():
	alphabet = string.ascii_lowercase + string.digits
	return '-'.join([''.join(choices(alphabet, k=4)) for i in range(3)])

def generate_token():
	alphabet = string.ascii_letters
	return ''.join(choices(alphabet, k=32))

def get_template_name(name):
	tpl_path = Path(current_app.root_path) / 'templates' / name
	if tpl_path.is_dir():
		tpl_path = tpl_path / 'default.html'
		name = f'{name}/default'
	else:
		tpl_path = Path(current_app.root_path) /  'templates' / f'{name}.html'

	if tpl_path.is_file():
		return f'{name}.html'
	else:
		return 'default.html'

def get_tipp_url(id):
	if "BASE_URL" in current_app.config:
		return f'{current_app.config["BASE_URL"]}/{id}'
	else:
		return url_for('web.show_tipp', id=id, _external=True)
	#return f'{current_app.config["BASEURL"]}/{id}'

def get_qr_url(id):
	if "BASE_URL" in current_app.config:
		return f'{current_app.config["BASE_URL"]}/{id}'
	else:
		return url_for('web.show_qr', id=id, _external=True)
	#return f'{current_app.config["BASEURL"]}/qr/{id}'

def create_tipp(body, id=None, template='default'):
	id = id if id else generate_id()

	raw_path = Path(current_app.config['RAWPATH']) / f'{id}.md'
	raw_path.write_text(body)

	qr_img = qrcode.make(get_tipp_url(id))
	qr_path = Path(current_app.config['QRPATH']) / f'{id}.png'
	qr_img.save(qr_path)

	compile_tipp(id, template=template)
	return id

def update_tipp(id, body, template=None):
	pass

def compile_tipp(id, template='default', body=None):
	if not body:
		raw_path = Path(current_app.config['RAWPATH']) / f'{id}.md'
		if raw_path.is_file():
			body = raw_path.read_text()

	if body:
		html_content = markdown.markdown(body, extensions=current_app.config['MARKDOWN']['extensions'])
		tpl_vars = {
			'baseurl':	current_app.config['SERVER_NAME'],
			'url':			get_tipp_url(id),
			'qrurl':		get_qr_url(id),
			'id': 			id,
			'content': 	Markup(html_content)
		}
		content = render_template(get_template_name(template), **tpl_vars)

		page_path = Path(current_app.config['PAGEPATH']) / f'{id}.html'
		page_path.write_text(content)
