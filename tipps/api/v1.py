from flask import Blueprint, request, current_app
import markdown
import qrcode

from tipps.db import get_db
from tipps.util import generate_id, get_template_name

def create_tipp(body, id=None, template='default'):
	id = id if id else generate_id()
	
	raw_path = Path(current_app.config['RAWPATH']) / f'{id}.md'
	raw_path.write_text(raw_content)
	
	qr_img = qrcode.make(f'{current_app.config["BASEURL"]}/{id}')
	qr_path = Path(current_app.config['QRPATH']) / f'{id}.png'
	qr_img.save(qr_path)
	
	compile_tipp(id, template=template)

def compile_tipp(id, template='default', body=None):
	template = get_template_name(template)
	
	if not body:
		raw_path = Path(current_app.config['RAWPATH']) / f'{id}.md'
		if raw_path.is_file():
			body = raw_path.read_text()
	
	if body:
		html_content = markdown.markdown(body, extensions=current_app.config['MARKDOWN']['extensions'])
		tpl_vars = {
			'baseurl':	current_app.config['BASEURL'],
			'url':			f'{current_app.config["BASEURL"]}/{id}',
			'qrurl':		f'{current_app.config["BASEURL""]}/qr/{id}',
			'id': 			id,
			'content': 	Markup(html_content)
		}
		content = render_template(get_template_name(template), **tpl_vars)
		
		page_path = Path(current_app.config['PAGEPATH']) / f'{id}.html'
		page_path.write_text(html)

v1 = Blueprint('api/v1', __name__, url_prefix='/api/v1')

@v1.route('/tipp/list', defaults={'token': None})
@v1.route('/tipp/list/<string:token>')
def list_tipps():
	details = bool(request.args['details']) if 'details' in request.args else False

	db = get_db()
	if token is None:
		result = db.execute('SELECT id,created,template FROM tipp').fetchall()
	else:
		result = db.execute('SELECT id,created,template FROM tipp INNER JOIN user ON user.id = tipp.user_id WHERE user.token = ?', (token,)).fetchall()
	
	tipps = []
	for row in result:
		tipp = {'id': row['id']}
		if details:
			tipp['url'] = f'{current_app.config["baseurl"]}/{row["id"]}'
			tipp['qrurl'] = f'{current_app.config["baseurl"]}/qr/{row["id"]}'
	return {'tipps': tipps}

@v1.route('/tipp/<string:id>')
def tipp_details(id):
	pass

@v1.route('/tipp/compile/<string:id>')
def tipp_details(id):
	compile_tipp(id)
