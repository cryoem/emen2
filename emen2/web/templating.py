'''\
It is possible to use templating engines other than Mako,
but none have been defined
'''

import os.path
try:
	import pkg_resources
	pkg_resources.require('Mako')
except ImportError:
	pass
from mako import exceptions
import mako.lookup
import mako.template
from emen2.util import fileops
import emen2.util.db_manipulation

class TemplateFactory(object):
	def __init__(self, default_engine_name, default_engine):
		self.__template_registry = {}
		self.register_template_engine(default_engine_name, default_engine)
		self.set_default_template_engine(default_engine_name)
		self.set_current_template_engine(default_engine_name)

	def render_template(self, name, context):
		template_engine = self.get_current_template_engine()
		return template_engine.render_template(name, context)

	def add_template(self, name, template_string):
		self.__currentengine.add_template(name, template_string)

	def has_template(self, name, engine=None, exc=False):
		if not engine:
			if exc:
				self.__currentengine[name]
				return True
			else:
				return self.__currentengine.has_template(name)
		else:
			self.__template_registry[engine].has_template(name)

	def set_default_template_engine(self, engine_name):
		self.__defaultengine = self.__template_registry[engine_name]

	def get_default_template_engine(self):
		return self.__defaultengine

	def set_current_template_engine(self, engine_name):
		self.__currentengine = self.__template_registry[engine_name]

	def get_current_template_engine(self):
		return self.__currentengine

	def register_template_engine(self, engine_name, engine):
		self.__template_registry[engine_name] = engine

	def handle_error(self, exception, context={}, errcode=500, template=None):
		return self.__currentengine.handle_error(exception)

	def template_engines(self):
		return  self.__template_registry.keys()
	template_registry = property(template_engines)

class TemplateNotFoundError(KeyError): pass
class AbstractTemplateLoader(object):
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
	def add_template(self, name, template_string):
		self.templates[name] = template_string
	def render_template(self, name, context):
		return self.templates[name]
	def has_template(self, name):
		return self.templates.has_template(name)
	def handle_error(self, exception):
		return str(exception)



class StandardTemplateEngine(AbstractTemplateEngine):
	def render_template(self, name, context):
		return self.templates[name].render(**context)


class MakoTemplateLoader(mako.lookup.TemplateCollection, AbstractTemplateLoader):
	templates = {}
	def __setitem__(self, name, value):
		if (not self.templates.has_key(name)) or (self[name].source != value):
			self.templates[name] = mako.template.Template(value, lookup=self, output_encoding='utf-8', encoding_errors='replace', filename=name)
	def get_template(self, uri, relativeto=None):
		try:
			return self[uri]
		except KeyError:
			raise TemplateNotFoundError('No Template: %s' % uri)





class MakoTemplateEngine(StandardTemplateEngine):
	templates = MakoTemplateLoader()

	def render_template(self, name, context):
		try:
			return self.templates[name].render_unicode(**context)
		except:
			return exceptions.html_error_template().render_unicode()

	def handle_error(self, exception, context={}, errcode=500, template=None):
		try: raise
		except Exception, e:
			g.log.msg("LOG_ERROR", "Error loader: %r" % e)
			if g.DEBUG:
				return exceptions.html_error_template().render_unicode()
			else:
				ctxt = dict(
					errmsg = '<br/><center>%s</center>' % e, def_title = 'Error',
					EMEN2WEBROOT = g.EMEN2WEBROOT, EMEN2DBNAME = g.EMEN2DBNAME,
					EMEN2LOGO = g.EMEN2LOGO, BOOKMARKS=g.BOOKMARKS,
					js_files = [], notify = '', ctxt=emen2.util.db_manipulation.Context()
				)
				ctxt.update(context)
				return self.render_template('/errors/simple_error', ctxt)



#### template loading
import emen2.db.config
g = emen2.db.config.g()

def template_callback(pwd, pth, mtch, name, ext, failures=None):
	#print pwd, pth
	if not hasattr(failures, 'append'): failures = []
	if ext == mtch:
		filpath = os.path.join(pwd[0], name)
		data = fileops.openreadclose(filpath+ext)
		templatename = os.path.join(pwd[0], name).replace(pth,'')
		level = 'LOG_INIT'
		msg = ["TEMPLATE ", templatename]
		try:
			g.templates.add_template(templatename,data)
		except BaseException, e:
			g.log(str(e))
			level = 'LOG_ERROR'
			msg[0] += 'FAILED'
			failures.append(templatename)
		else:
			msg[0] += 'LOADED'
		msg.append(filpath+ext)
		g.log.msg(level, ': '.join(msg))

get_templates = fileops.walk_paths('.mako', template_callback)
