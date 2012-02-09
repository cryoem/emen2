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
	"2.0rc5": "software_113",
	"2.0rc6": "software_114"
}

import os.path
def prefix(pref, strs):
	return [os.path.join(pref, name) for name in strs]



if __name__ == "__main__":
	# Base
	packages = [
		'emen2',
		'emen2.db',
		'emen2.web',
		'emen2.util',
		'twisted.plugins'
		]
		
	package_data = {			
		'emen2.db': ['config.base.json', 'skeleton.json', 'base.json'],
		'emen2.web': ['static/*.*', 'static/*/*.*', 'static/*/*/*.*', 'static/*/*/*/*.*'],
		'twisted': ['plugins/emen2_plugin.py']
	}
	
	exts = ['base', 'default', 'em', 'eman2', 'site']
	for ext in exts:
		packages.append('emen2.exts.%s'%ext)
		packages.append('emen2.exts.%s.views'%ext)
		package_data['emen2.exts.%s'%ext] = ['json/*.json', 'templates/*.mako', 'templates/*/*.mako', 'templates/*/*/*.mako']

	setup(
		name='emen2',
		version=VERSION,
		description='EMEN2 Object-Oriented Scientific Database',
		author='Ian Rees',
		author_email='ian.rees@bcm.edu',
		url='http://blake.grid.bcm.edu/emanwiki/EMEN2/',
		download_url="%s/%s/emen2-%s.tar.gz"%(URLBASE, URLMAP.get(VERSION,'daily'), VERSION),
		packages=packages,
		package_data=package_data
	)


	# 'emen2.exts.base': prefix('web/static', ),
