from __future__ import with_statement

import copy
import atexit
import hashlib
import operator
import os
import sys
import time
import traceback
import collections
import itertools
import random
import cPickle as pickle
import bsddb3
import demjson
import weakref

from functools import partial, wraps

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

import emen2.util.utils


class MethodUtil(object):
	def doc(self, func, *args, **kwargs):
		return func.__doc__



class DBProxy(object):
	"""Proxy container for database. Implements the public APIs. All clients use the proxy instead of the database instance directly.9"""
	__publicmethods = {}
	__adminmethods = {}
	__extmethods = {}

	@classmethod
	def _allmethods(cls):
		return set(cls.__publicmethods) | set(cls.__extmethods)


	def __init__(self, db=None, dbpath=None, ctxid=None, host=None, ctx=None, txn=None):
		
		import database
		
		self.__txn = None
		self.__bound = False

		if not db:
			db = database.DB(path=dbpath)

		self.__db = weakref.proxy(db)

		self.__ctx = ctx
		self.__txn = txn


	def __enter__(self):
		#g.debug('beginning DBProxy context')
		self.__oldtxn = self.__txn
		self.__txn = self.__db.txncheck(txn=self.__txn, ctx=self.__ctx)
		#g.debug('self.__oldtxn: %r :: self.__txn: %r' % (self.__oldtxn, self.__txn))
		return self


	#@g.log.debug_func
	def __exit__(self, type, value, traceback):
		#g.debug('ending DBProxy context')
		#g.debug('self.__oldtxn: %r :: self.__txn: %r' % (self.__oldtxn, self.__txn))
		if self.__oldtxn is not self.__txn:
			if type is None: self._committxn()
			else:
				g.log_error('DBProxy.__exit__: type=%s, value=%s, traceback=%s' % (type, value, traceback))
				self._aborttxn()
			self.__txn = None
		self.__oldtxn = None


	def _gettxn(self):
		return self.__txn

	def _settxn(self, txn=None):
		self.__txn = txn

	def _starttxn(self):
		self.__txn = self.__db.newtxn(self.__txn)

	def _committxn(self):
		self.__db.txncommit(txn=self.__txn)
		self.__txn = None

	def _aborttxn(self):
		if self.__txn:
			self.__db.txnabort(txn=self.__txn)
		self.__txn = None


	def _login(self, username="anonymous", password="", host=None):

		try:
			host = host or self.__ctx.host
		except:
			host = None

		try:
			ctxid = self.__db._login(username=username, password=password, host=host, ctx=self.__ctx, txn=self.__txn) #host
			self._setcontext(ctxid=ctxid, host=host)

		except:
			if self.__txn: self._aborttxn()
			raise

		return ctxid


	def _setcontext(self, ctxid=None, host=None):
		try:
			self.__ctx = self.__db._getcontext(ctxid=ctxid, host=host, txn=self.__txn)
			self.__ctx.setdb(db=self)
			#g.log.msg('LOG_DEBUG', "\nDBProxy._setcontext results:")
			#g.log.msg('LOG_DEBUG', "self ",hex(id(self)))
			#g.log.msg('LOG_DEBUG', "self.__ctx ", self.__ctx)
			#g.log.msg('LOG_DEBUG', "self.__ctx.db ", self.__ctx.db)
			#g.log.msg('LOG_DEBUG', "self.__ctx.ctxid ", self.__ctx.ctxid)
			#g.log.msg('LOG_DEBUG', "self.__ctx.username ", self.__ctx.username)
			#g.log.msg('LOG_DEBUG', "self.__ctx.groups ", self.__ctx.groups)
			#g.log.msg('LOG_DEBUG', "self.__ctx.grouplevels ", self.__ctx.grouplevels)
			#g.log.msg('LOG_DEBUG', "self.__db ", self.__db)
			#g.log.msg('LOG_DEBUG', "self.__txn ", self.__txn)
			#g.log.msg('LOG_DEBUG', "\n\n")


		except:
			self.__ctx = None
			if self.__txn: self._aborttxn()
			raise

		self.__bound = True
		return self


	def _clearcontext(self):
		if self.__bound:
			self.__ctx = None
			self.__bound = False



	@property
	def _bound():
		return self.__bound
	@_bound.deleter
	def _bound():
		self._clearcontext()



	def _ismethod(self, name):
		if name in self._allmethods(): return True
		return False



	@classmethod
	def _register_publicmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		#g.log.msg('LOG_INIT', "REGISTERING PUBLICMETHOD (%s)" % name)
		cls.__publicmethods[name] = func

	@classmethod
	def _register_adminmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		#g.log.msg('LOG_INIT', "REGISTERING ADMINMETHOD (%s)" % name)
		cls.__adminmethods[name] = func



	@classmethod
	def _register_extmethod(cls, name, refcl):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		#g.log.msg('LOG_INIT', "REGISTERING EXTENSION (%s)" % name)
		cls.__extmethods[name] = refcl



	def _callmethod(self, method, args, kwargs):
		args = list(args)
		method = method.split('.')
		func = getattr(self, method[0])
		result = None
		if len(method) > 1:
			result = getattr(MethodUtil(), method[1])(func, args, kwargs)
		else:
			result = func(*args, **kwargs)
		return result


	def _getctx(self):
		return self.__ctx

	def _wrapmethod(self, func):
		@wraps(func)
		def _inner(*args, **kwargs):
			with self:
				result = func(*args, **kwargs)
			return result
		return _inner

	def __getattribute__(self, name):
		result = None
		#g.log('getattr -> self: %r -> name: %r' % (self, name))
		if name.startswith('__') and name.endswith('__'):
			try:
				result = getattr(self.__db, name)
			except:
				result = object.__getattribute__(self, name)
			return result
		elif name.startswith('_'):
			result = object.__getattribute__(self, name)

		elif name in self._allmethods():
			kwargs = dict(ctx=self.__ctx, txn=self.__txn)
			if result is None:
				result = self.__publicmethods.get(name)

			if result:
				result = partial(result, self.__db, **kwargs)

			else:
				result = self.__extmethods.get(name)()

				kwargs['db'] = self.__db
				if result:
					result = partial(result.execute, **kwargs)


			result = wraps(result.func)(result)

		else:
			raise AttributeError('No such attribute %s of %r' % (name, self.__db))

		return result





# Wrapper methods for public API and admin API methods
def publicmethod(func):
	"""Decorator for public API database method"""
	@wraps(func)
	def _inner(self, *args, **kwargs):
		#g.debug('entering func: %r' % func)

		result = None
		txn = kwargs.get('txn')
		ctx = kwargs.get('ctx')
		commit = False

		if txn is False:
			txn = None
		elif bool(txn) is False:
			txn = self.newtxn()
			commit = True
		kwargs['txn'] = txn

		try:
			#t = time.time()
			#g.debug('func: %r, args: %r, kwargs: %r' % (func, args, kwargs))
			result = func(self, *args, **kwargs)
			#g.debug('func: %r... done result: %r' % (func,result))
			#g.debug("-> %0.4f %s"%((time.time()-t)*1000, func.func_name))

		except Exception, e:
			# traceback.print_exc(e)
			if commit is True:
				txn and self.txnabort(ctx=ctx, txn=txn)
			raise

		else:
			if commit is True:
				#g.log('committing, func left: %r txn: %r' % (func,txn) )
				txn and self.txncommit(ctx=ctx, txn=txn)

		#g.debug('leaving func: %r' % func)
		return result

	DBProxy._register_publicmethod(func.func_name, _inner)
	return _inner




def adminmethod(func):
	"""Decorator for public admin API database method"""

	if not func.func_name.startswith('_'):
		DBProxy._register_adminmethod(func.func_name, func)

	@wraps(func)
	def _inner(*args, **kwargs):
		ctx = kwargs.get('ctx')
		if ctx is None:
			ctx = [x for x in args is isinstance(x, emen2.Database.user.User)] or None
			if ctx is not None: ctx = ctx.pop()
		if ctx.checkadmin():
			return func(*args, **kwargs)
		else:
			raise emen2.Database.exceptions.SecurityError, 'No Admin Priviliges'
	return _inner




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
		DBProxy._register_extmethod(cls.__methodname__, cls) #cls.__name__, cls.__methodname__, cls



# ian: register all public methods
# import database

