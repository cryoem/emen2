from __future__ import with_statement

import os
import sys
import time
import traceback
import weakref
import functools
import collections

import emen2.db.config
g = emen2.db.config.g()


import emen2.db.vartypes
import emen2.db.macros
import emen2.db.properties






def publicmethod(*args, **kwargs):
	"""Decorator for public admin API database method"""
	def _inner(func):
		emen2.db.proxy.DBProxy._register_publicmethod(func, *args, **kwargs)
		return func
	return _inner





class MethodUtil(object):
	allmethods = set(['help'])
	def help(self, func, *args, **kwargs):
		return func.__doc__



# def __request(self, methodname, params):
#     # call a method on the remote server
#
#     request = dumps(params, methodname, encoding=self.__encoding,
#                     allow_none=self.__allow_none)
#
#     response = self.__transport.request(
#         self.__host,
#         self.__handler,
#         request,
#         verbose=self.__verbose
#         )
#
#     if len(response) == 1:
#         response = response[0]
#
#     return response
#


class _Method(object):
	# Taken from XML-RPC lib to support nested methods
	def __init__(self, proxy, name):
		self._proxy = proxy
		self._name = name

	def __getattr__(self, name):
		func = self._proxy._publicmethods.get("%s.%s"%(self._name, name))
		if func:
			return self._proxy._wrap(func)
		return _Method(self._proxy, "%s.%s" % (self._name, name))


	def __call__(self, *args):
		raise AttributeError, "No public method %s"%self._name

class MethodTree(collections.MutableMapping):
	def __init__(self, **kwargs):
		self.__storage = {}
		self.__value = None
	def __setitem__(self, name, value):
		key, div, cont = name.partition('.')
		if key not in self.__storage:
			self.__storage[key] = MethodTree()
		if not cont:
			self.__storage[key].__value = value
		else:
			self.__storage[key][cont] = value
	def __getitem__(self, name):
		result = self.__storage
		while name:
			key, _, name = name.partition('.')
			result = result[key]
		return result
	def __delitem__(self, name):
		raise NotImplementedError, 'not implemented yet'
	def __iter__(self):
		return iter(self.__storage)
	def __len__(self):
		return len(self.__storage)
	def get_value(self):
		return self.__value


class DBProxy(object):
	"""A proxy that provides access to database public methods and handles low level details, such as Context and transactions.

	db = DBProxy()
	db._login(username, password)

	"""

	_publicmethods = {}

	@classmethod
	def _allmethods(cls):
		return set(cls._publicmethods)


	def __init__(self, db=None, dbpath=None, ctxid=None, host=None, ctx=None, txn=None):
		# it can cause circular imports if this is at the top level of the module
		import database

		self.__txn = None
		self.__bound = False

		if not db:
			db = database.DB(path=dbpath) # path will default to g.EMEN2DBHOME

		self.__db = db
		# weakref.proxy(db)

		self.__ctx = ctx
		self.__txn = txn

		#"with" interface state
		self.__txnflags = None
		self.__oldtxn = None
		self.__contextvars = None
		self.__oldctx = ctx


	# Implements "with" interface
	def _settxnflags(self, flags):
		self.__txnflags = flags
		return self

	def _setctxflags(self, ctxid, host):
		self.__contextvars = (ctxid, host)
		return self



	def __enter__(self):
		self.__oldctx = self.__ctx
		self.__oldtxn = self.__txn
		self.__txn = self.__db.txncheck(txn=self.__txn, ctx=self.__ctx, flags=self.__txnflags)
		if self.__contextvars:
			self.__setContext(*self.__contextvars)
		#g.debug('txn', self.__txn, self.__oldtxn)
		#g.debug('ctx', self.__ctx, self.__oldctx)
		return self


	def __exit__(self, type, value, traceback):
		if self.__oldtxn is not self.__txn:
			if type is None:
				g.log_info('DBProxy.__exit__: committing Transaction')
				self._committxn()
			else:
				g.log_error('DBProxy.__exit__: type=%s, value=%s, traceback=%s' % (type, value, traceback))
				self._aborttxn()
			self.__txn = None
			self.__oldtxn = None
			self.__txnflags = None
		self._clearcontext()
		self.__ctx = self.__oldctx
		if self.__ctx != None: self.__bound = True
		self.__contextvars = None
		self.__oldctx = None


	# Transactions
	def _gettxn(self):
		return self.__txn


	def _settxn(self, txn=None):
		self.__txn = txn


	def _starttxn(self, flags=None):
		self.__txn = self.__db.newtxn(self.__txn, flags=flags)
		return self


	def _committxn(self):
		self.__db.txncommit(txn=self.__txn)
		self.__txn = None


	def _aborttxn(self):
		if self.__txn:
			self.__db.txnabort(txn=self.__txn)
		self.__txn = None


	# Rebind a new Context
	def _setContext(self, ctxid=None, host=None):
		with self:
			self.__setContext(ctxid, host)
	def __setContext(self, ctxid, host):
		g.debug('txn:', self.__txn)
		try:
			self.__ctx = self.__db._getcontext(ctxid=ctxid, host=host, txn=self.__txn)
			self.__ctx.setdb(db=self)
		except:
			self.__ctx = None
			raise

		self.__bound = True
		return self


	def _clearcontext(self):
		if self.__bound:
			self.__ctx = None
			self.__bound = False


	def _getctx(self):
		return self.__ctx


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
	def _register_publicmethod(cls, func, apiname, write=False, admin=False, ext=False):
		# print "Registering func: %s"%apiname
		# if set([func.apiname, func.func_name]) & cls._allmethods():
		# 	raise ValueError('''method %s already registered''' % name)
		setattr(func, 'apiname', apiname)
		setattr(func, 'write', write)
		setattr(func, 'admin', admin)
		setattr(func, 'ext', ext)

		cls._publicmethods[func.apiname] = func
		cls._publicmethods[func.func_name] = func



	def _callmethod(self, method, args, kwargs):
		"""Call a method by name with args and kwargs (e.g. RPC access)"""
		args = list(args)
		method = method.rsplit('.',1)
		if len(method) > 1 and method[1] not in MethodUtil.allmethods:
			method[0] = '%s.%s' % (method[0], method.pop())
		if len(method) == 1: method.append('')

		func = getattr(self, method[0])
		result = None
		if method[1]:
			result = getattr(MethodUtil(), method[1])(func, args, kwargs)
		else:
			result = func(*args, **kwargs)

		return result



	def __getattr__(self, name):
		func = self._publicmethods.get(name)
		if func: return self._wrap(func)
		return _Method(self, name)


	# ian: changed how publicmethods are created because docstrings and tracebacks were being mangled
	# they are now wrapped when accessed, not replaced with pre-wrapped versions.

	# >>> def my_decorator(f):
	# ...     @wraps(f)
	# ...     def wrapper(*args, **kwds):
	# ...         print 'Calling decorated function'
	# ...         return f(*args, **kwds)
	# ...     return wrapper
	# ...
	# >>> @my_decorator
	# ... def example():
	# ...     """Docstring"""
	# ...     print 'Called example function'
	# ...


	def _wrap(self, func):
		# print "going into wrapper for func: %s / %s"%(func.func_name, func.apiname)
		kwargs = dict(ctx=self.__ctx, txn=self.__txn)

		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			# t = time.time()
			result = None
			commit = False
			ctx = self.__ctx
			kwargs['ctx'] = ctx

			if func.admin and not ctx.checkadmin():
				raise Exception, "This method requires administrator level access."

			txn = self.__txn
			if bool(txn) is False:
				txn = self.__db.newtxn()
				commit = True
			kwargs['txn'] = txn

			if func.ext:
				kwargs['db'] = self.__db

			# print 'func: %r, args: %r, kwargs: %r'%(func, args, kwargs)

			try:
				# result = func.execute(*args, **kwargs)
				result = func(self.__db, *args, **kwargs)

			except Exception, e:
				# traceback.print_exc(e)
				if commit is True:
					txn and self.__db.txnabort(ctx=ctx, txn=txn)
				raise

			else:
				if commit is True:
					txn and self.__db.txncommit(ctx=ctx, txn=txn)

			# timer!
			# print "---\t\t%10d ms: %s"%((time.time()-t)*1000, func.func_name)
			return result

		return wrapper


