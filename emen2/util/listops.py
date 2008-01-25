def get(collection, key, default=None):
	try:
		return collection[key]
	except KeyError:
		return default
	except IndexError:
		return default