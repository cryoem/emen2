import json
import emen2.db.globalns
g = emen2.db.globalns.GlobalNamespace()

def encode(obj, **kwargs):
	g.log.msg('LOG_DEBUG', 'kwargs: %s' % kwargs)
	def encode_preprocess(obj):
		if hasattr(obj, 'json_equivalent'): obj = obj.json_equivalent()
		outp = None
		if hasattr(obj, '__iter__'):
			if hasattr(obj, 'items'):
				outd = {}
				for k,v in obj.items():
					outd[encode_preprocess(k)] = encode_preprocess(v)
				outp = outd
			else:
				outl = []
				for i in obj:
					outl.append(encode_preprocess(i))
				outp = outl
		else:
			outp = obj
		return outp
	return json.dumps(encode_preprocess(obj))

decode = json.loads
