# $Id$

from __future__ import with_statement, print_function
import yaml
import jsonrpc.jsonutil
import emen2.db.config
import getpass

#g.logger.set_state('CRITICAL')
parser = emen2.db.config.DBOptions()
parser.add_option('--flowstyle', dest='flowstyle', action='store', default='full', help='yaml flowstyle to use: ')
parser.add_option('-f', '--file', dest='file', action='store')
parser.add_option('-k', '--key', dest='keys', action='append')
parser.add_option('-w', '--write', dest='ofile', action='store')
parser.add_option('-g', '--get', dest='get', action='store', help='get value')
parser.add_option('-S', '--set', dest='set', action='store', help='set value')
parser.add_option('-i', '--inline', dest='inline', action='store_true', help='change inline', default=False)
parser.add_option('-j', '--json', dest='json', action='store_true', help='return value as json (only for -g)', default=False)
parser.add_option('', '--interactive', dest='json', action='store_true', help='return value as json (only for -g)', default=False)
v, args = parser.parse_args(lc=False)
parser.load_config(loglevel='CRITICAL')

kwargs = {}
if v.flowstyle.isdigit(): v.flowstyle = int(v.flowstyle)
elif v.flowstyle.lower() == 'full': kwargs['fs'] = 0
elif v.flowstyle.lower() in ('medium','none'): kwargs['fs'] = None
elif v.flowstyle.lower() == 'compact': kwargs['fs'] = 1

if v.file is not None: kwargs['file'] = v.file
if v.keys is not None: kwargs['kg'] = v.keys
if v.set:
	if len(args) != 2: raise ValueError, 'wrong number of arguments'
	emen2.db.config.globalns.setattr(args[0], yaml.safe_load(args[1]))

if v.get:
	val = emen2.db.config.globalns.getattr(v.get)
	if v.json: print(jsonrpc.jsonutil.encode(val))
	else: print(val)

else:
	out = emen2.db.config.globalns.to_yaml(**kwargs)
	if v.ofile and v.file is None:
		with file(v.ofile, 'w') as f:
			f.write(out)
	elif v.set and v.file and v.inline:
		with file(v.file, 'w') as f:
			f.write(out)
	else:
		print(out)

__version__ = "$Revision$".split(":")[1][:-1].strip()
