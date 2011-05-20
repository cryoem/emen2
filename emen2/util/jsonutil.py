# $Id$
"""
primary purpose is to allow more types to be serialized by simplejson
"""

try:
	import json
except ImportError:
	import simplejson as json

from emen2.util.decorators import make_decorator

def dict_encode(obj):
	return dict( (encode.func(k),encode.func(v)) for k,v in obj.iteritems() )

def list_encode(obj):
	return list(encode.func(i) for i in obj)

def safe_encode(obj):
	'''Always return something, even if it is useless for serialization'''
	try: json.dumps(obj)
	except TypeError: obj = str(obj)
	return obj

@make_decorator(json.dumps)
def encode_(obj, *a, **kw):
	obj = getattr(obj, 'json_equivalent', lambda: obj)()
	func = lambda x: x
	if hasattr(obj, 'items'):
		func = dict_encode
	elif hasattr(obj, '__iter__'):
		func = list_encode
	else:
		func = safe_encode
	return func(obj)

decode_ = json.loads

encode, decode = encode_, decode_

__version__ = "$Revision$".split(":")[1][:-1].strip()
