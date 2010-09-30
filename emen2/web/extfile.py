import emen2.db.config
g = emen2.db.config.g()
import random

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


# ian: todo: optimize this some in the future; not every page needs all the files
class BaseJS(ExtFile):
	def init(self):
		super(BaseJS, self).init()


		self.files = [
			self.dbtree.reverse('TemplateRender', '/js/datatypes.js'),
			self.dbtree.reverse('TemplateRender', '/js/settings.js'),
			'%s/static/js/jquery/jquery.js'%g.EMEN2WEBROOT,
			'%s/static/js/jquery/jquery-ui.js'%g.EMEN2WEBROOT,
			'%s/static/js/jquery/jquery.html5_upload.js'%g.EMEN2WEBROOT,
			'%s/static/js/jquery/jquery.json.js'%g.EMEN2WEBROOT,
			'%s/static/js/jquery/jquery.colorPicker.js'%g.EMEN2WEBROOT,
			'%s/static/js/util.rec.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.browser.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.comments.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.edit.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.editdefs.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.file.js?v=%s'%g.EMEN2WEBROOT
			'%s/static/js/w.find.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.mapselect.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.permission.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.query.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.relationship.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.table.js?v=%s'%g.EMEN2WEBROOT,
			'%s/static/js/w.tile.js?v=%s'%g.EMEN2WEBROOT,
			]


class BaseCSS(ExtFile):
	def init(self):
		super(BaseCSS, self).init()
		self.files = [
			self.dbtree.reverse('TemplateRender', '/css/main.css'),
			'%s/static/css/custom-theme/jquery-ui-1.8.2.custom.css' % g.EMEN2WEBROOT
		]
