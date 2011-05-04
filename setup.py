import os
import subprocess

from distutils.core import setup

from emen2 import VERSION
URLBASE = "http://ncmi.bcm.edu/ncmi/software/EMEN2"
URLMAP = {
	"daily": "software_94",
	"2.0rc1": "software_105",
	"2.0rc2": "software_107",
	"2.0rc3": "software_108",
	"2.0rc4": "software_110",	
	"2.0rc5": "software_110"
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


static_files = \
	filterwalk('emen2/static', filetypes=['.png', '.gif', '.css', '.js', '.jpg', '.ico', '.txt']) +  \
	filterwalk('emen2/templates', filetypes=['.mako']) + \
	filterwalk('emen2/skeleton', filetypes=['.json'])
	# filterwalk('emen2/clients/emdash/ui', filetypes=['.ui'])



# import distutils.command.build_ext
# class build_test(distutils.command.build_ext.build_ext):
# 	description = "Build against Berkeley DB and bsddb3"
# 	def run(self):
# 		# this method will need to liberally copy and paste from the parent class, and insert one or two changes...




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
			'emen2.util',
			'jsonrpc',
			'emdash',
			'emdash.ui'
			],
		package_data={
			'emen2': static_files
			},
		scripts=[
			'scripts/emen2control.py',
			'scripts/emen2client.py'
			]
		)


