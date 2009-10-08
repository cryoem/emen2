from functools import partial

def get(collection, key, default=None):
	try: return collection[key]
	except KeyError: return default
	except IndexError: return default

def remove(collection, keys):
	if not hasattr(keys, '__iter__'):
		keys = [keys]
	for key in keys:
		try: del collection[key]
		except KeyError: pass

def adj_list(list, items):
	list.extend(items)
	return list

def adj_dict(dict, items):
	dict.update(items)
	return dict

def combine_dicts(*args):
	result = dict()
	for dct in args: result.update(dct)
	return result

def combine_lists(sep=' ', *args):
	return (sep.join(x) for x in zip(*args))

def filter_dict(dict, allowed, pred):
	result = {}
	[ result.update([(key, dict[key])]) for key in dict if pred(key, set(allowed)) ]
	return result

pick = partial(filter_dict, pred=(lambda x,y: x in y))
drop = partial(filter_dict, pred=(lambda x,y: x not in y))

def chunk(list, grouper=lambda x: x[0]==x[1]):
   result = [[list[0]]]
   for x in xrange(len(list)-1):
      window = list[x:x+2]
      if not grouper(window):
         result.append([])
      result[-1].append(window[1])
   return result


def test_get():
	print '1 == ',  get( {2:2, 3:3, 1:1}, 1 )
	print '1 == ', get( {2:2, 3:3}, 1, 1 )
	print 'None == ', get( {2:2, 3:3}, 1)

def run_tests():
	test_get()

if __name__ == '__main__':
	run_tests()
