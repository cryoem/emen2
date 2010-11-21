import os
from distutils.core import setup

def filterwalk(path, filetypes=None):
	filetypes = filetypes or []
	ret = []
	for i in os.walk(path):		

		base = i[0].split(os.sep)[1:]
		if base:
			base = os.path.join(*base)
		else:
			base = ''
		
		for j in i[2]:
			ext = os.path.splitext(j)[-1]
			if filetypes and ext not in filetypes:
				continue
			ret.append(os.path.join(base, j))

	return ret
	
	
static_files =  filterwalk('web/static', filetypes=['.png', '.gif', '.css', '.js', '.jpg', '.ico', '.txt']) + filterwalk('web/templates', filetypes=['.mako'])

setup(
	name='emen2',
	version='2.0',
	description='EMEN2 Object-Oriented Scientific Database',
	author='Ian Rees',
	author_email='ian.rees@bcm.edu',
	url='http://ncmi.bcm.edu/',	
	package_dir={'':'..'},
	packages=[
		'emen2',
		'emen2.db',
		'emen2.web',
		'emen2.web.resources',
		'emen2.web.views',
		'emen2.skeleton',
		'emen2.clients',
		'emen2.clients.emdash',
		'emen2.clients.emdash.models',
		'emen2.clients.emdash.threads',
		'emen2.clients.emdash.ui'
		],
	package_data={
		'emen2.db': ['config.base.json'], 
		'emen2.clients.emdash': ['emdash-start.bat'],
		'emen2.web': static_files
		},
	scripts=[
		'emen2control.py', 
		'emen2client.py', 
		'clients/emdash/emdash.py', 
		]
	)