import os
import subprocess

from distutils.core import setup

VERSION = "2.0rc1"
URLBASE = "http://ncmi.bcm.edu/ncmi/software/EMEN2"
URLMAP = {
	"daily": "software_94",
	"2.0rc1": "software_105"
}

SCPBASE="10.10.9.104:/homes/www/Zope-2.7.0/var/extdata/reposit/ncmi/software/EMEN2"

def upload(v):
	infile = "dist/emen2-%s.tar.gz"%v
	dest = "%s/%s"%(SCPBASE, URLMAP[v])
	p = subprocess.Popen(["scp", infile, dest])
	sts = os.waitpid(p.pid, 0)
	
	
	
def filterwalk(path, filetypes=None):
	filetypes = filetypes or []
	ret = []
	for i in os.walk(path):		

		base = i[0]
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
	
	

static_files =  filterwalk('emen2/static', filetypes=['.png', '.gif', '.css', '.js', '.jpg', '.ico', '.txt']) + filterwalk('emen2/templates', filetypes=['.mako'])

if __name__ == "__main__":
	setup(
		name='emen2',
		version=VERSION,
		description='EMEN2 Object-Oriented Scientific Database',
		author='Ian Rees',
		author_email='ian.rees@bcm.edu',
		url='http://blake.grid.bcm.edu/emanwiki/EMEN2/',	
		download_url="%s/%s/emen2-%s.tar.gz"%(URLBASE, URLMAP[VERSION], VERSION),
		packages=[
			'emen2',
			'emen2.db',
			'emen2.web',
			'emen2.web.resources',
			'emen2.web.views',
			'emen2.skeleton',
			'emen2.util',
			'emen2.clients',
			'emen2.clients.emdash',
			'emen2.clients.emdash.models',
			'emen2.clients.emdash.threads',
			'emen2.clients.emdash.ui'
			],
		package_data={
			'emen2.db': ['config.base.json'],
			'emen2': static_files
			},
		scripts=[
			'scripts/emen2control.py', 
			'scripts/emen2client.py', 
			'scripts/emdash.py', 
			]
		)


