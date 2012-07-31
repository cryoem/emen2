import os
import subprocess
from distutils.core import setup

import emen2

if __name__ == "__main__":
    # Base
    packages = [
        'emen2',
        'emen2.db',
        'emen2.web',
        'emen2.util',
        # 'twisted'
        ]
        
    package_data = {            
        'emen2.db': ['config.base.json', 'skeleton.json', 'base.json', 'bulk.c'],
        'emen2.web': ['static/*.*', 'static/*/*.*', 'static/*/*/*.*', 'static/*/*/*/*.*'],
        # 'twisted': ['plugins/emen2_plugin.py'] #emen2_plugin.py
    }
    
    scripts = ['scripts/emen2ctl']
    
    exts = ['base', 'default', 'em', 'site', 'publicdata']
    for ext in exts:
        packages.append('emen2.exts.%s'%ext)
        packages.append('emen2.exts.%s.views'%ext)
        package_data['emen2.exts.%s'%ext] = ['json/*.json', 'templates/*.mako', 'templates/*/*.mako', 'templates/*/*/*.mako']

    setup(
        name='emen2',
        version=emen2.__version__,
        description='EMEN2 Object-Oriented Scientific Database',
        author='Ian Rees',
        author_email='ian.rees@bcm.edu',
        url='http://blake.grid.bcm.edu/emanwiki/EMEN2/',
        packages=packages,
        package_data=package_data,
        scripts=scripts,
        zip_safe=False
    )
