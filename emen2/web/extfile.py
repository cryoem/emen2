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


# ian: todo: optimize this some in the future; not every page needs all the files
class BaseJS(ExtFile):
	def init(self):
		super(BaseJS, self).init()
		self.files = [
			self.dbtree.reverse('TemplateRender', '/basedb/datatypes.js'),
			self.dbtree.reverse('TemplateRender', '/basedb/settings.js'),
			'%s/js/jquery/jquery.js'%g.EMEN2WEBROOT,
			'%s/js/jquery/jquery-ui.js'%g.EMEN2WEBROOT,
			'%s/js/jquery/jquery.html5_upload.js'%g.EMEN2WEBROOT,
			'%s/js/jquery/jquery.json.js'%g.EMEN2WEBROOT,
			'%s/js/jquery/jquery.colorPicker.js'%g.EMEN2WEBROOT,
			'%s/js/util.admin.js'%g.EMEN2WEBROOT,
			'%s/js/util.json.js'%g.EMEN2WEBROOT,
			'%s/js/util.query.js'%g.EMEN2WEBROOT,
			'%s/js/util.rec.js'%g.EMEN2WEBROOT,
			'%s/js/util.reverse.js'%g.EMEN2WEBROOT,
			'%s/js/w.browser.js'%g.EMEN2WEBROOT,
			'%s/js/w.comments.js'%g.EMEN2WEBROOT,
			'%s/js/w.edit.js'%g.EMEN2WEBROOT,
			'%s/js/w.find.js'%g.EMEN2WEBROOT,
			'%s/js/w.mapselect.js'%g.EMEN2WEBROOT,
			'%s/js/w.paramdef.js'%g.EMEN2WEBROOT,
			'%s/js/w.permission.js'%g.EMEN2WEBROOT,
			'%s/js/w.query.js'%g.EMEN2WEBROOT,
			'%s/js/w.recorddef.js'%g.EMEN2WEBROOT,
			'%s/js/w.relationship.js'%g.EMEN2WEBROOT,
			'%s/js/w.table.js'%g.EMEN2WEBROOT,
			'%s/js/w.tile.js'%g.EMEN2WEBROOT,

			'%s/js/w.popup.js'%g.EMEN2WEBROOT,

			'%s/js/w.file.js'%g.EMEN2WEBROOT
			]


class BaseCSS(ExtFile):
	def init(self):
		super(BaseCSS, self).init()
		self.files = [
			'%s/css/custom-theme/jquery-ui-1.8.2.custom.css' % g.EMEN2WEBROOT, 
			'%s/css/main.css' % g.EMEN2WEBROOT
			# '%s/css/style.css' % g.EMEN2WEBROOT
		]
