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

from functools import partial, wraps

import emen2.globalns
import emen2.util.utils

g = emen2.globalns.GlobalNamespace('')





class DBProxy(object):
	"""Proxy container for database. Implements the public APIs. All clients use the proxy instead of the database instance directly.9"""
	__publicmethods = {}
	__adminmethods = {}
	__extmethods = {}

	@classmethod
	def _allmethods(cls):
		return set(cls.__publicmethods) | set(cls.__extmethods)


	def __init__(self, db=None, dbpath=None, importmode=False, ctxid=None, host=None, ctx=None, txn=None):
		self.__txn = None
		self.__bound = False
		
		if not dbpath:
			dbpath = g.EMEN2DBPATH

		if not db:
			self.__db = database.DB(dbpath, importmode=importmode)
		else:
			self.__db = db

		self.__ctx = ctx
		self.__txn = txn		


	def __enter__(self):
		self.__oldtxn = self.__txn
		self.__txn = self.__db.txncheck(txn=self.__txn, ctx=self.__ctx)
		return self


	def __exit__(self, type, value, traceback):
		if self.__oldtxn is not self.__txn:
			if type is None: self._committxn()
			else: self._aborttxn()
		del self.__oldtxn


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
			ctxid = self.__db._login(username=username, password=password, host=host, ctx=self.__ctx, txn=self.__txn) #host
			self._setcontext(ctxid=ctxid, host=host)

		except:
			if self.__txn: self._aborttxn()
			raise

		return ctxid


	def _setcontext(self, ctxid=None, host=None):
		#print "setting context.. %s %s"%(ctxid, host)
		try:
			self.__ctx = self.__db._getcontext(ctxid=ctxid, host=host, txn=self.__txn)
			self.__ctx.setdb(db=self)
			#self.__ctx.db = self

		except:
			self.__ctx = None

			if self.__txn: self._aborttxn()
			raise

		self.__bound = True


	def _clearcontext(self):
		if self.__bound:
			self.__ctx = None
			self.__bound = False



	@emen2.util.utils.prop.init
	def _bound():
		def fget(self): return self.__bound
		def fdel(self): self._clearcontext()
		return dict(fget=fget, fdel=fdel)



	def _ismethod(self, name):
		if name in self._allmethods(): return True
		return False



	@classmethod
	def _register_publicmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		g.log.msg('LOG_INIT', "REGISTERING PUBLICMETHOD (%s)" % name)
		cls.__publicmethods[name] = func

	@classmethod
	def _register_adminmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		g.log.msg('LOG_INIT', "REGISTERING ADMINMETHOD (%s)" % name)
		cls.__adminmethods[name] = func



	@classmethod
	def _register_extmethod(cls, name, refcl):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		g.log.msg('LOG_INIT', "REGISTERING EXTENSION (%s)" % name)
		cls.__extmethods[name] = refcl



	def _callmethod(self, method, args, kwargs):
		args = list(args)
		return getattr(self, method)(*args, **kwargs)


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

		if name.startswith('__') and name.endswith('__'):
			try:
				result = getattr(self.__db, name)
			except:
				result = object.__getattribute__(self, name)
			return result
		elif name.startswith('_'):
			return object.__getattribute__(self, name)


		kwargs = {}
		kwargs["ctx"] = self.__ctx
		kwargs["txn"] = self.__txn

		result = None

		if name in self._allmethods():

			result = None

			#t = time.time()
			#print "-> ",name
			
			#if 'admin' in self.__ctx.groups:
			#	result = self.__adminmethods.get(name)

			if result is None:
				result = self.__publicmethods.get(name)

			if result:
				result = wraps(result)(partial(result, self.__db, **kwargs))

			else:
				result = self.__extmethods.get(name)()

				kwargs['db'] = self.__db
				if result:
					result = partial(result.execute, **kwargs)


			result = wraps(result.func)(result)
			#print "-> %s %s"%(name, (time.time()-t)*1000)

		else:
			raise AttributeError('No such attribute %s of %r' % (name, self.__db))

		return result






# Wrapper methods for public API and admin API methods
def publicmethod(func):
	"""Decorator for public API database method"""
	@wraps(func)
	def _inner(self, *args, **kwargs):

		
		result = None
		txn = kwargs.get('txn')
		ctx = kwargs.get('ctx')
		commit = False


		if txn is None:
			txn = self.newtxn()
			commit = True
		kwargs['txn'] = txn


		try:
			# t = time.time()
			result = func(self, *args, **kwargs)
			# print "%s %s"%((time.time()-t)*1000, func.func_name)

		except Exception, e:
			# traceback.print_exc(e)
			if commit is True:
				txn and self.txnabort(ctx=ctx, txn=txn)
			raise

		else:
			if commit is True:
				txn and self.txncommit(ctx=ctx, txn=txn)

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
			ctx = [x for x in args is isinstance(x, emen2.Database.dataobjects.user.User)] or None
			if ctx is not None: ctx = ctx.pop()
		if ctx.checkadmin():
			return func(*args, **kwargs)
		else:
			raise emen2.Database.subsystems.exceptions.SecurityError, 'No Admin Priviliges'
	return _inner


import database

