import types
import md5
import random


class HTMLTab():
	def __init__(self,d=None):
		self.classname = None
		self.active = None
		self.content = {}
		self.labels = {}
		self.href = {}
		self.js = {}
		self.order = []
		self.switched = 1

		if isinstance(d,dict):
			self.__dict__.update(d)
			self.check()

		if isinstance(d,HTMLTab):
			self.__dict__.update(d.__dict__)
			self.check()

	def addtab(self, name, content=None):
		self.content[name]=content

	def removetab(self, name):
		try: del self.content[name]
		except: pass

	def setcontent(self, name, content=None):
		self.content[name]=content

	def setorder(self, order):
		self.order = list(order)

	def setactive(self, active):
		self.active = active

	def autoorder(self):
		if not self.order:# or self.order == [None]:
			self.order = self.content.keys()
		self.order = sorted(list(self.order))
		if not self.order:
			self.order = []
		# or [None]

	def autoactive(self):
		if not self.order:
			self.autoorder()
		if len(self.order) > 0:
			self.active = self.order[0]
		else:
			self.active = None

	def setlabel(self, name, title):
		self.labels[name]=title
		if title==None and self.labels.has_key(name):
			del self.labels[name]

	def sethref(self, name, href):
		self.href[name]=href
		if href==None and self.href.has_key(name):
			del self.href[name]

	def setjs(self, name, action):
		self.js[name]=action
		if action==None and self.js.has_key(name):
			del self.js[name]

	def getclass_buttons(self):
		return "buttons"%self.classname

	def getclass_pages(self):
		return "pages"%self.classname

	def getclass_button(self, name):
		if name==self.active:
			return "button button_active button_%s button_%s_active"%(self.classname, self.classname)
		return "button button_%s"%self.classname

	def getclass_page(self, name):
		if name==self.active:
			return "page page_active page_%s page_%s_active"%(self.classname, self.classname)
		return "page page_%s"%self.classname

	#id="buttons_main" class="buttons buttons_main"
	def getid_buttons(self):
		return "buttons_%s"%self.classname

	def getid_button(self, name):
		return "button_%s_%s"%(self.classname,name)

	def getid_page(self, name):
		return "page_%s_%s"%(self.classname,name)

	def getid_pages(self):
		return "pages_%s"%self.classname

	def getclassname(self):
		return self.classname

	def setclassname(self, name):
		self.classname=name

	def getcontent_button(self, name):
		if self.href.get(name):
			return """<a href="%s">%s</a>"""%(self.href.get(name),self.labels.get(name,name))
		return self.labels.get(name,name)

	def getcontent_page(self, name):
		# accept funcs as content; main reason is that mako caller.body() will write directly to context when it's called, so we just pass the func reference and call it here
		c = self.content.get(name)
		if type(c) == types.FunctionType:
			c = c()
		return c or ""

	def getjs_button(self, name):
		if self.href.get(name):
			return ""
		if self.switched:
			return """ onclick="javascript:switchin('%s','%s');" """%(self.classname, name)
		if self.js.get(name):
			return """ onclick="javascript:%s" """%(self.js.get(name))
		return ""

	def check(self):
		alltabs = set(self.content.keys() + self.labels.keys() + self.href.keys() + self.order + [self.active]) - set([None])

		if not self.classname:
			self.classname=md5.md5.hexdigest("%s%s"%(random.random(),alltabs))

		if not self.order:
			self.autoorder()
		if not self.active:
			self.autoactive()

		#print "cls: %s"%self.classname
		#print "\talltabs: %s"%alltabs
		#print "\tcontent: %s"%self.content
		#print "\torder: %s"%self.order
		#print "\tactive: %s"%self.active

