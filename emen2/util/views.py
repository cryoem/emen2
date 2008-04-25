from cPickle import loads, dumps
from emen2.TwistSupport_html.publicresource import PublicView
from emen2.subsystems import routing
from emen2.util.utils import adj_dict
from emen2.util.db_manipulation import DBTree
from functools import partial

import emen2.debug as _d
d = _d.DebugState()

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

def process_item(item):
	url = item['menu_target']
	if item['menu_name'] != None:
		name = item['menu_name']
		args, kwargs = loads(item['menu_arguments'] or dumps(((), {})))
		url = '/db'+routing.URLRegistry.reverselookup(name, *args, **kwargs)
	elif item['menu_link'] != None:
		url = item['menu_link']
	return url

def build_menus(toplevels, db, **dbinfo):
	getrecord = partial(db.getrecord, **dbinfo)
	menus = []
#	try: 
	toplevels = getrecord(toplevels)
	for menu in toplevels:
		items = menu['order']
		if items == None:
			items = db.getchildren(menu.recid, keytype='record', **dbinfo)
		items = getrecord(items)	
		i_list = []
		for item in items:
			label = item['menu_label']
			i_list.append(( label,process_item(item) ))
		menus.append([menu['menu_label'], i_list])
#	finally:
	return menus

def register_view(name, bases, dict):
	cls = type(name, bases, dict)
	if unicode(cls.__matcher__) != cls.__matcher__:
		PublicView.register_url(cls.__name__, cls.__matcher__[0])(cls)
		counter = 1
		for expression in cls.__matcher__:
			PublicView.register_url('%s%02d' %( cls.__name__, counter ), expression)(cls)
			counter += 1
	else:
		PublicView.register_url(cls.__name__, cls.__matcher__)(cls)
	return cls

class View(object):
	'''Base Class for views, no intrinsic functionality
	subclasses should define an __init__ method 
	which takes the arguments the match returns
	and a __str__ method which returns the
	rendered view. Also, subclasses MUST call
	View.__init__!!!'''
	
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

class Page(object):
	def __init__(self, template, db, ctxid, value_dict=None, host=None, **kwargs):
		self.__template = template
		self.__valuedict = {'menus': build_menus(g.PAGE_MENUS, db=db, ctxid=ctxid, host=host)}
		self.__valuedict.update(adj_dict(value_dict or {}, kwargs))
		
	def __unicode__(self):
		return g.templates.render_template(self.__template, self.__valuedict)
	
	def __str__(self):
		return g.templates.render_template(self.__template, self.__valuedict).encode('ascii', 'replace')
	
	@classmethod
	def render_template(cls, template, db, ctxid, title='', content='', modifiers=None):
		return cls(template, db, ctxid, content=content, title=title, value_dict=modifiers)
	@classmethod
	def quick_render(cls, db, ctxid, title='', content='', modifiers=None):
		return cls.render_template('/pages/page', db, ctxid, title, content)

