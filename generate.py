# -*- coding: utf-8 -*-
import string
import qrcode
from pathlib import Path
from random import choices

alphabet = string.ascii_lowercase + string.digits

def generate_id():
	return '-'.join([''.join(choices(alphabet, k=4)) for i in range(3)])

def generate_from_text(body, id=None, template='default'):
	jinja = jinja2.Environment(
		loader=jinja2.FileSystemLoader(f'{config["basepath"]}/templates')
	)

	id = id if id else generate_id()

	# save raw md data
	with open(f'{config["basepath"]}/raw/{id}.md', 'w') as rawfile:
		rawfile.write(body)

	# generate url and qrcode
	url = f'{config["baseurl"]}/{id}'
	qrurl = f'{config["baseurl"]}/qr/{id}'
	code = qrcode.make(url)
	code.save(f'{config["basepath"]}/qrcodes/{id}.png')

	# get template
	tpl = jinja.get_template(get_template_name(template))

	# generate html and build template
	#html_body = markdown2.markdown(body, extras=['header-ids', 'nofollow', 'tables'])
	html_body = markdown.markdown(body, extensions=['tables'])

	tpl_vars = {
		'baseurl': config['baseurl'],
		'url': url,
		'qrurl': qrurl,
		'id': id,
		'content': html_body
	}

	html = tpl.render(**tpl_vars)
	with open(f'{config["basepath"]}/pages/{id}.html', 'w') as htmlfile:
		htmlfile.write(html)

text = '''
# Kleiner Test

![](https://i.ytimg.com/vi/dft5MExg0sM/maxresdefault.jpg)

Was [ist mit](http://ngb.schule) direktem <strong>HTML</strong> <code>Code</code>?

<math>f(x) = 4x^2 - 3x</math>

> Hier ein kleiner Satz.

## Gehen Tabellen?

| A | B | C | D | E |
|---|---|---|---|---|
|   |   |   |   |   |
|   |   |   |   |   |
|   |   |   |   |   |

## Collapse

<div class="collapse">
  <input type="checkbox" id="collapse-section1" checked aria-hidden="true">
  <label for="collapse-section1" aria-hidden="true">Collapse section 1</label>
  <div>
    <p>This is the first section of the collapse</p>
  </div>
  <input type="checkbox" id="collapse-section2" aria-hidden="true">
  <label for="collapse-section2" aria-hidden="true">Collapse section 2</label>
  <div>
    <p>This is the second section of the collapse</p>
  </div>
</div>
'''
generate_from_text(text, id='test')
