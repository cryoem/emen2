# $Id$

import json
import xmlrpclib
import urllib2

import emen2.db.config
g = emen2.db.config.g()

if not g.getattr('CONFIG_LOADED', False):
	try:
		parser = emen2.db.config.DBOptions()
		parser.parse_args()
	except:
		raise

import emen2
import getpass
db = emen2.opendb()
ruser = user = g.getprivate('USERNAME') or 'root'
rpasswd = passwd = g.getprivate('ROOTPW')
if not passwd:
	passwd = getpass.getpass()
db._login(user, passwd)

# if not raw_input('same remote credentials? ').lower().startswith('y'):
# 	print '''\
# Change:
# 	1. username?
# 	2. password?
# ?''',
# 	if raw_input('').strip() == '1': ruser = raw_input('remote username? ')
# 	else: rpasswd = raw_input('remote password? ')

rdb = xmlrpclib.ServerProxy('http://ncmi.bcm.tmc.edu/challenge/RPC2/')
# ctxid = rdb._login(ruser, rpasswd)

g.log_info('updating paramdefs')
paramdefs = rdb.getparamdefnames()
paramdefs = (rdb.getparamdef(x) for x in paramdefs if not x.lower().startswith('file'))
for pd in paramdefs: db.putparamdef(pd)
g.log_info('updating recorddefs')
recorddefs = rdb.getrecorddefnames()
recorddefs = (rdb.getrecorddef(x) for x in recorddefs if not x.lower().startswith('file'))
for rd in recorddefs: db.putrecorddef(rd)

def puttree(keytype, root):
	jsonrequest = json.dumps( dict(keys=root, keytype=keytype, recurse=10000) )
	jsonresponse = urllib2.urlopen('http://ncmi.bcm.tmc.edu/challenge/json/getchildtree', jsonrequest)
	def closure():
		tree = json.load(jsonresponse)
		return ( (elem,child) for elem in tree for child in tree[elem] )
	tree = closure()
	for elem, child in tree: db.pclink(elem, child, keytype=keytype)

g.log_info('setting paramdef tree')
db._starttxn()
puttree('paramdef', 'root')
db._committxn()

g.log_info('setting recorddef tree')
db._starttxn()
puttree('recorddef', 'root')
db._committxn()

g.log_info('done')
__version__ = "$Revision$".split(":")[1][:-1].strip()
