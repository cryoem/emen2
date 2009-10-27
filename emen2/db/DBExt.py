from __future__ import with_statement

import DBProxy
#g = emen2.globalns.GlobalNamespace('')



class DBExt(object):
	"""Database extension"""

	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls

	@classmethod
	def register(cls):
		"""Register database extension decorator"""
		DBProxy.DBProxy._register_extmethod(cls.__methodname__, cls) #cls.__name__, cls.__methodname__, cls



