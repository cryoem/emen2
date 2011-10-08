# # $Id$
# from emen2.web.view import View
# 
# 
# @View.register
# class Wiki(record.Record):
# 
# 	@View.add_matcher(r'^/wiki/(?P<name>.+)/$')
# 	def init(self, name=None):
# 		self._init(name=name, children=False, parents=False)
# 		self.template = '/pages/wiki.main'
# 		self.set_context_item("rendered",self.db.renderview(self.rec, viewtype="mainview"))
# 
# 
# 	# @View.add_matcher(r'^/wiki/(?P<page>.+)/edit/$')
# 	# def edit(self, page=None):
# 	# 	self._init(name=page, children=False, parents=False)
# 	# 	self.template = '/pages/wiki.edit'
# 	# 	self.set_context_item("rendered",self.db.renderview(self.rec, viewtype="mainview", mode="htmledit"))
# 	#
# 
# 
# 
# __version__ = "$Revision$".split(":")[1][:-1].strip()
