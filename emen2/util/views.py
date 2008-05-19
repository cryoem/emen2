from emen2.TwistSupport_html.publicresource import PublicView
from emen2.util.db_manipulation import DBTree

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


class View(object):
	'''Base Class for views, sets up the instance variables for the class
	
	Subclasses are required to do two things:
		- have a class attribute called __metaclass__ which is equal to View.register_view
		- call View.__init__ in the __init__ methods
	'''
	ctxid = property(lambda self: self.__ctxid)
	host = property(lambda self: self.__host)
	db = property(lambda self: self.__db)
	username = property(lambda self: self.__username)
	pw = property(lambda self: self.__pw)
	mimetype = property(lambda self: self.__mimetype)
	dbtree = property(lambda self: self.__dbtree)
	def __init__(self, ctxid, host, db=None, username=None, pw=None, mimetype='text/html; charset=utf-8'):
		'''subclasses should remember to call the base classes __init__ method'''
		self.__ctxid = ctxid
		self.__host = host
		self.__db = db
		self.__username = username
		self.__pw = pw
		self.__mimetype = mimetype
		self.__dbtree = DBTree(db, ctxid, host)
	
	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls
	
	@classmethod
	def register(cls):
		print 'REGISTERING: %r' % cls
		if unicode(cls.__matcher__) != cls.__matcher__:
			PublicView.register_url(cls.__name__, cls.__matcher__[0])(cls)
			counter = 1
			for expression in cls.__matcher__:
				PublicView.register_url('%s%02d' %( cls.__name__, counter ), expression)(cls)
				counter += 1
		else:
			PublicView.register_url(cls.__name__, cls.__matcher__)(cls)

	def __iter__(self):
		'''returns (result, mimetype)'''
		if self.mimetype.split('/') == 'text':
			return iter((unicode(self), self.__mimetype))
		else:
			return iter((str(self), self.__mimetype))
		
	def __unicode__(self):
		'''returns the data'''
		return unicode(self.get_data())
	
	def __str__(self):
		try:
			return str(self.get_data())
		except UnicodeDecodeError:
			return self.get_data()
	
	def get_data(self):
		return 'No Data'
#### Backwards-compatibility #######
register_view = View.register_view       #
##############################

class Page(object):
	'''Abstracts template rendering, possisbly useless'''
	def __init__(self, template, **kwargs):
		self.__template = template
		self.__valuedict = {}
		self.__valuedict.update(kwargs)
		
	def __unicode__(self):
		return g.templates.render_template(self.__template, self.__valuedict)
	
	def __str__(self):
		return g.templates.render_template(self.__template, self.__valuedict).encode('ascii', 'replace')
	
	@classmethod
	def render_template(cls, template, title='', content='', modifiers=None):
		return cls(template, content=content, title=title, value_dict=modifiers)
	@classmethod
	def quick_render(cls,  title='', content='', modifiers=None):
		return cls.render_template('/pages/page', title, content)

