import emen2.util.utils
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')
import emen2.subsystems.routing


class ExtFileLibrary(object):
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


	@emen2.util.utils.prop.init
	def files():
		fget = lambda self: self.__files
		def fset(self, value):
			if not hasattr(value, '__iter__'):
				value = [value]
			self.__files.extend(value)
		return dict(fget=fget, fset=fset)

	def __init__(self, dbtree):
		self.__files = []
		self.dbtree = dbtree
		self.init()

	def init(self): pass

	def __iter__(self):
		return iter(self.__files)

class BaseJS(ExtFileLibrary):
	__metaclass__ = ExtFileLibrary.registerjs
	def init(self):
		self.files = [
			'%s/js/jquery/jquery.js' % g.EMEN2WEBROOT,
			self.dbtree.reverse('TemplateRender', '/base/settings.js'),
			'%s/js/reverse.js' % g.EMEN2WEBROOT,
		]
		super(BaseJS, self).init()

class BaseCSS(ExtFileLibrary):
	__metaclass__ = ExtFileLibrary.registercss
	def init(self):
		self.files = ['%s/css/style.css' % g.EMEN2WEBROOT]
		super(BaseCSS, self).init()


