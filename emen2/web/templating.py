# $Id$
'''\
It is possible to use templating engines other than Mako,
but none have been defined
'''

import time
import os
import stat
import collections

import mako
import mako.lookup
import mako.template
from mako import exceptions

from emen2.util import fileops

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

	def __init__(self, ctxt):
		self._files = []
		self.ctxt = ctxt
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
			'jquery/jquery.jsonrpc.js',
			'jquery/jquery.fullcalendar.js',
			'jquery/jquery.fullcalendar-gcal.js',
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
			"record.js",
			"util.js",
			'calendar.js'
			]

		self.files = [
			self.ctxt.reverse('TemplateRender', t='/js/settings.js'),
			]
		for i in addfiles:
			self.files.append('%s/static-%s/js/%s'%(g.EMEN2WEBROOT, emen2.VERSION, i))


class BaseCSS(ExtFile):
	def init(self):
		super(BaseCSS, self).init()
		addfiles = [
			'custom-theme/jquery-ui-1.8.2.custom.css',
			'base.css',
			'style.css',
			'boxer.css',
			'fullcalendar.css'
		]

		self.files = []
		for i in addfiles:
			self.files.append('%s/static-%s/css/%s'%(g.EMEN2WEBROOT, emen2.VERSION, i))

		self.files.append(self.ctxt.reverse('TemplateRender', t='/css/map.css'))






class TemplateFactory(object):
	def __init__(self, default_engine_name, default_engine):
		self.templates = default_engine

	def render_template(self, name, context):
		return self.templates.render_template(name, context)

	def add_template(self, name, template_string, path):
		self.templates.add_template(name, template_string, path)

	def has_template(self, name, engine=None, exc=False):
		return self.templates.has_template(name)

	def handle_error(self, exception, context={}, errcode=500, template=None):
		return self.templates.handle_error(exception)



class TemplateNotFoundError(KeyError):
	pass



class AbstractTemplateLoader(object):#collections.Mapping):
	'''template loaders are dictionary like objects'''
	templates = {}

	def __getitem__(self, name):
		try:
			return self.templates[name]
		except KeyError:
			raise TemplateNotFoundError(name)

	def __setitem__(self, name, value):
		self.templates[name] = value

	def has_template(self, name):
		return self.templates.has_key(name)



class AbstractTemplateEngine(object):
	'''Useless Example Implementation of a Template Engine'''
	templates = AbstractTemplateLoader()

	def get_template(self, name):
		return self.templates[name]
	__getitem__ = get_template

	def add_template(self, name, template_string, path):
		self.templates[name] = (template_string, path)

	def render_template(self, name, context):
		return self.get_template(name)

	def has_template(self, name):
		return self.templates.has_template(name)

	def handle_error(self, exception):
		return str(exception)



class StandardTemplateEngine(AbstractTemplateEngine):
	def render_template(self, name, context):
		return self.templates[name].render(**context)



class Template(object):

	@staticmethod
	def tempconst(value, lookup, filename):
		return mako.template.Template(value, lookup=lookup, output_encoding='utf-8', encoding_errors='replace', filename=filename)

	def __init__(self, value, lookup, filename, path):
		self.path = path
		self.filename = filename
		self.mtime = os.stat(path).st_mtime
		self.template = self.tempconst(value, lookup, filename=filename)

	def update(self, lookup):
		try:
			mtime = os.stat(self.path).st_mtime
			if int(mtime) != int(self.mtime):
				self.mtime = mtime
				g.debug('updating template: %s' % self.filename)
				with file(self.path) as f:
					self.template = self.tempconst(f.read(), lookup, filename=self.filename)
		except OSError, e:
			if e.errno == 2: g.error('file (%r) no longer exists, not updating template %s' % (self.path, self.filename))
			else: g.error('problem with template %s: %s' % (self.filename, e))



class MakoTemplateLoader(mako.lookup.TemplateCollection, AbstractTemplateLoader):
	templates = {}

	def __setitem__(self, name, value):
		template, path = value
		if True:
		#if (not self.templates.has_key(name)):# or (self[name].source != value):
			try:
				self.templates[name] = Template(template, self, name, path)
			except:
				self.templates[name] = Template('', self, name, path)
				raise

	def get_template(self, uri, relativeto=None):
		try:
			template = self[uri]
			if g.DEBUG: template.update(self)
			return self[uri].template
		except KeyError:
			raise TemplateNotFoundError('No Template: %s' % uri)



class MakoTemplateEngine(StandardTemplateEngine):
	templates = MakoTemplateLoader()

	def render_template(self, name, context):
		try:
			return self.templates.get_template(name).render_unicode(**context)
		except:
			return exceptions.html_error_template().render_unicode()

	# ian: this is just handled inside emen2resource for now..
	def handle_error(self, exception, context={}, errcode=500, template=None):
		try:
			raise
		except Exception, e:
			g.error("Error loader: %r" % e)
			if g.DEBUG:
				return exceptions.html_error_template().render_unicode()
			else:
				ctxt = emen2.web.view.Context()
				ctxt = dict(
					errmsg = '<br/><center>%s</center>' % e, title = 'Error',
					EMEN2WEBROOT = g.EMEN2WEBROOT, EMEN2DBNAME = g.EMEN2DBNAME,
					EMEN2LOGO = g.EMEN2LOGO, BOOKMARKS=g.BOOKMARKS,
					HOST = None,
					js_files = BaseJS(ctxt), notify = '', ctxt=ctxt,
					css_files = BaseCSS(ctxt),
				)
				ctxt.update(context)
				return self.render_template('/errors/error', ctxt)


def chomp(st, len_):
	if len(st) > len_:
		st = st[-(len_-3):]
		st = ''.join(['...', st])
	return st

#### template loading
def template_callback(pwd, pth, mtch, name, ext, failures=None):
	# print pwd, pth
	if not hasattr(failures, 'append'):
		failures = []

	assert ext == mtch#:

	filpath = os.path.join(pwd[0], name)
	data = fileops.openreadclose(filpath+ext)
	templatename = os.path.join(pwd[0], name).replace(pth,'')
	msg = ["TEMPLATE ", templatename]
	level = 'DEBUG'

	try:
		g.templates.add_template(templatename,data,filpath+ext)
	except BaseException, e:
		g.info(str(e))
		level = 'ERROR'
		msg[0] += 'FAILED'
		failures.append(templatename)
	else:
		msg[0] += 'LOADED'

	msg.append(chomp(filpath+ext, 60))
	g.log.msg(level, ': '.join(msg))




get_templates = fileops.walk_paths('.mako', template_callback)



__version__ = "$Revision$".split(":")[1][:-1].strip()
