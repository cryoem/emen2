import emen2.db.config
g = emen2.db.config.g()


class ExtFile(object):
	def __register(registry):
		@staticmethod
		def _inner(name, bases, dict):
			newcls = type(name, bases, dict)
			registry[name] = newcls
			return newcls
		return _inner

	css_registry = {}
	registercss = __register(css_registry)

	js_registry = {}
	registerjs = __register(js_registry)


	@property
	def files(self):
		return self.__files

	@files.setter
	def files(self, value):
		if not hasattr(value, '__iter__'):
			value = [value]
		self.__files.extend(value)

	def __init__(self, dbtree):
		self.__files = []
		self.dbtree = dbtree
		self.init()

	def init(self): pass

	def __iter__(self):
		return iter(self.__files)


class BaseJS(ExtFile):
	__metaclass__ = ExtFile.registerjs
	def init(self):
		self.files = [
			'%s/js/jquery/jquery.js' % g.EMEN2WEBROOT,
			'%s/js/reverse.js' % g.EMEN2WEBROOT,
		]
		if self.dbtree is not None:
			self.files.append(self.dbtree.reverse('TemplateRender', '/basedb/settings.js'))
		super(BaseJS, self).init()


class BaseCSS(ExtFile):
	__metaclass__ = ExtFile.registercss
	def init(self):
		self.files = ['%s/css/style.css' % g.EMEN2WEBROOT]
		super(BaseCSS, self).init()


