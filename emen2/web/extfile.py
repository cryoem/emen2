# $Id$
import emen2.db.config
g = emen2.db.config.g()

class ExtFile(object):
	def _register(registry):
		@staticmethod
		def _inner(name, bases, dict):
			newcls = type(name, bases, dict)
			registry[name] = newcls
			return newcls
		return _inner

	css_registry = {}
	registercss = _register(css_registry)

	js_registry = {}
	registerjs = _register(js_registry)


	def addfile(self, f):
		self.files.append('%s/static/%s'%(g.EMEN2WEBROOT, f)) #, g.VERSION

	@property
	def files(self):
		return self._files

	@files.setter
	def files(self, value):
		if not hasattr(value, '__iter__'):
			value = [value]
		self._files.extend(value)

	def __init__(self, dbtree):
		self._files = []
		self.dbtree = dbtree
		self.init()

	def init(self): pass

	def __iter__(self):
		return iter(self._files)



# ian: todo: optimize this some in the future; not every page needs all the files
class BaseJS(ExtFile):
	def init(self):
		super(BaseJS, self).init()

		addfiles = [
			'jquery/jquery.js',
			'jquery/jquery-ui.js',
			'jquery/jquery.json.js',
			'jquery/jquery.timeago.js',
			"calendar.js",
			"comments.js",
			"edit.js",
			"editdefs.js",
			"file.js",
			"find.js",
			"permission.js",
			"query.js",
			"relationship.js",
			"table.js",
			"tile.js",
			"util.js",
			"test.js",
			]

		self.files = [self.dbtree.reverse('TemplateRender', t='/js/settings.js')]
		for i in addfiles:
			self.files.append('%s/static-%s/js/%s'%(g.EMEN2WEBROOT, emen2.VERSION, i))


class BaseCSS(ExtFile):
	def init(self):
		super(BaseCSS, self).init()
		addfiles = [
			'custom-theme/jquery-ui-1.8.2.custom.css',
			'main.css',
			'colors.css',
			'boxer.css',
			'calendar.css'
		]

		self.files = []
		for i in addfiles:
			self.files.append('%s/static-%s/css/%s'%(g.EMEN2WEBROOT, emen2.VERSION, i))
			
		self.files.append(self.dbtree.reverse('TemplateRender', t='/css/main.css'))



__version__ = "$Revision$".split(":")[1][:-1].strip()
