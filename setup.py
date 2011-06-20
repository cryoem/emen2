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

if __name__ == "__main__":
	setup(
		name='emen2',
		version=VERSION,
		description='EMEN2 Object-Oriented Scientific Database',
		author='Ian Rees',
		author_email='ian.rees@bcm.edu',
		url='http://blake.grid.bcm.edu/emanwiki/EMEN2/',
		download_url="%s/%s/emen2-%s.tar.gz"%(URLBASE, URLMAP.get(VERSION,'daily'), VERSION),
		packages=[
			'emen2',
			'emen2.db',
			'emen2.web',
			'emen2.web.resources',
			'emen2.web.views',
			'emen2.util',
			],
		package_data={
			'emen2': ['templates/*.mako', 'templates/.*', 'templates/*/*.mako', 'templates/*/*/*.mako', 'static/*.*', 'static/*/*.*', 'static/*/*/*.*', 'static/*/*/*/*.*'],
			'emen2.db': ['config.base.json', 'skeleton.json'],
		},
		scripts=['scripts/emen2control.py']
	)
