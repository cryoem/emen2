def if_caching(f):
	def _inner(*args, **kwargs):
		if args[0].caching: return f(*args, **kwargs)
		else: pass
	return _inner

def cache(f):
	def _inner(*args, **kwargs):
		self = args[0]
		cargs = [ (tuple(x) if hasattr(x,'__iter__') else x) for x in args]
		ckey = self.get_cache_key(f.func_name, *cargs[1:], **kwargs)
		if ckey is not None:
			hit, result = self.check_cache(ckey)
			if hit: return result
		result = f(*args, **kwargs)
		if result and ckey is not None:
			self.store(ckey, result)
		return result
	return _inner


class CacheMixin:
	def reset_cache(self): self.cache = {}
	
	def start_caching(self): 
		self.caching = True
		self.reset_cache()
	
	def stop_caching(self):
		self.caching = False
		self.reset_cache()
		
	def toggle_caching(self):
		self.caching = not self.caching
	
	@if_caching
	def get_cache_key(self, *args, **kwargs): 
		return (args, tuple(kwargs.items()))
	
	@if_caching
	def store(self, key, result): self.cache[key] = result

	@if_caching
	def check_cache(self, key):
		result = False, None
		if self.cache.has_key(key): 
			result = True, self.cache[key]
		return result
