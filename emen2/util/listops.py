def get(collection, key, default=None):
	try:
		return collection[key]
	except KeyError:
		return default
	except IndexError:
		return default
	
def remove(collection, keys):
	if not hasattr(keys, '__iter__'):
		keys = [keys]
	for key in keys:
		try:
			del collection[key]
		except KeyError:
			pass

def adj_dict(dict, items):
	dict.update(items)
	return dict

def combine_dicts(*args):
	result = dict()
	for dct in args:
		result.update(dct)
	return result
	
def combine_lists(sep=' ', *args):
	return (sep.join(x) for x in zip(*args))

def test_get():
	print '1 == ',  get( {2:2, 3:3, 1:1}, 1 )
	print '1 == ', get( {2:2, 3:3}, 1, 1 )
	print 'None == ', get( {2:2, 3:3}, 1)

def run_tests():
	test_get()

if __name__ == '__main__':
	run_tests()