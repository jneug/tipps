from Flask import current_app

alphabet = string.ascii_lowercase + string.digits

def generate_id():
	return '-'.join([''.join(choices(alphabet, k=4)) for i in range(3)])

def get_template_name(name):
	tpl_path = Path(current_app.instance_path) / 'templates' / name
	if tpl_path.is_dir():
		tpl_path = tpl_path / 'default.html'
		name = f'{name}/default'
	else:
		tpl_path = Path(current_app.instance_path) /  'templates' / f'{name}.html'

	if tpl_path.is_file():
		return f'{name}.html'
	else:
		return 'default.html'
