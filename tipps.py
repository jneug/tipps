# -*- coding: utf-8 -*-
import string
from random import choices
from flask import Flask, request, abort, send_file, render_template, redirect, url_for
from markupsafe import Markup
import re
from pathlib import Path
import markdown
import qrcode
import jinja2

app = Flask(__name__)

config = {
	'basepath': 	'.',
	'pagespath': 	'pages',
	'qrpath': 		'qrcodes',
	'rawpath': 		'raw',
	'baseurl': 		'http://127.0.0.1:5000',
	'markdown': 	{
		'extensions': ['tables']
	}
}

alphabet = string.ascii_lowercase + string.digits

def generate_id():
	return '-'.join([''.join(choices(alphabet, k=4)) for i in range(3)])

def get_template_name(name):
	tpl_path = Path(config['basepath']) / 'templates' / name
	if tpl_path.is_dir():
		tpl_path = tpl_path / 'default.html'
		name = f'{name}/default'
	else:
		tpl_path = Path(config['basepath']) / 'templates' / f'{name}.html'

	if tpl_path.is_file():
		return f'{name}.html'
	else:
		return 'default.html'

@app.route('/list')
def list_tipps():
	pages_path = Path(config['basepath']) / config['pagespath']
	pagelist = sorted(pages_path.glob('*.html'))
	pages = []
	for page in pagelist:
		pages.append(str(page))
	return ({'pages': pages}, 200)

@app.route('/<string:id>')
def show_tipp(id):
	#if re.fullmatch(r'[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}', id):
	qrcode_path = Path(config['basepath']) / config['pagespath'] / f'{id}.html'
	if qrcode_path.is_file():
		return send_file(qrcode_path, mimetype='text/html')
	else:
		abort(404)

@app.route('/qr/<string:id>')
def show_qr(id):
	qrcode_path = Path(config['basepath']) / config['qrpath'] / f'{id}.png'
	if qrcode_path.is_file():
		return send_file(qrcode_path, mimetype='image/png')
	else:
		abort(404)

@app.route('/compile/<string:id>', methods=['GET'])
def compile_by_id(id):
	if 'template' in request.args:
		template = request.args['template']
	else:
		template = 'default'

	raw_path = Path(config['basepath']) / config['rawpath'] / f'{id}.md'
	if raw_path.is_file():
		raw_content = raw_path.read_text()
		html_content = markdown.markdown(raw_content, extensions=config['markdown']['extensions'])

		tpl_vars = {
			'baseurl':	config['baseurl'],
			'url':			f'{config["baseurl"]}/{id}',
			'qrurl':		f'{config["baseurl"]}/qr/{id}',
			'id': 			id,
			'content': 	Markup(html_content)
		}
		html = render_template(get_template_name(template), **tpl_vars)

		page_path = Path(config['basepath']) / config['pagespath'] / f'{id}.html'
		page_path.write_text(html)

		return ({
			'id': id,
			'url': tpl_vars['url'],
			'qr': tpl_vars['qrurl']
		}, 200)
	else:
		abort(404)

@app.route('/compile',  methods=['POST'])
def compile_from_text():
	if 'template' in request.args:
		template = request.args['template']
	else:
		template = 'default'

	id = generate_id()

	raw_content = request.data.decode().strip()
	if len(raw_content) == 0:
		abort(403)
	html_content = markdown.markdown(raw_content, extensions=config['markdown']['extensions'])

	tpl_vars = {
		'baseurl':	config['baseurl'],
		'url':			f'{config["baseurl"]}/{id}',
		'qrurl':		f'{config["baseurl"]}/qr/{id}',
		'id': 			id,
		'content': 	Markup(html_content)
	}
	html = render_template(get_template_name(template), **tpl_vars)

	raw_path = Path(config['basepath']) / config['rawpath'] / f'{id}.md'
	raw_path.write_text(raw_content)
	page_path = Path(config['basepath']) / config['pagespath'] / f'{id}.html'
	page_path.write_text(html)

	qr_img = qrcode.make(tpl_vars['url'])
	qr_path = Path(config['basepath']) / config['qrpath'] / f'{id}.png'
	qr_img.save(qr_path)

	return ({
		'id': id,
		'url': tpl_vars['url'],
		'qr': tpl_vars['qrurl']
	}, 200)

def compile(text, id=None, template='default'):
	id = id if id else generate_id()


if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host='0.0.0.0',port=9018)
