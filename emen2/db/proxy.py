from __future__ import with_statement

import os
import sys
import time
import traceback
import weakref
import functools

import emen2.db.config
g = emen2.db.config.g()


class MethodUtil(object):
	def doc(self, func, *args, **kwargs):
		return func.__doc__



class DBProxy(object):
	"""A proxy that provides access to database public methods and handles low level details, such as Context and transactions.
	
	db = DBProxy()
	db._login(username, password)
	
	"""
	
	__publicmethods = {}
	__adminmethods = {}
	__extmethods = {}

	@classmethod
	def _allmethods(cls):
		return set(cls.__publicmethods) | set(cls.__extmethods)


	def __init__(self, db=None, dbpath=None, ctxid=None, host=None, ctx=None, txn=None):
		
		# it can cause circular imports if this is at the top level of the module
		import database
		
		self.__txn = None
		self.__bound = False

		if not db:
			db = database.DB(path=dbpath) # path will default to g.DB_HOME
		self.__db = db
		# weakref.proxy(db)

		self.__ctx = ctx
		self.__txn = txn

	
	# Implements "with" interface
	def __enter__(self):
		#g.debug('beginning DBProxy context')
		self.__oldtxn = self.__txn
		self.__txn = self.__db.txncheck(txn=self.__txn, ctx=self.__ctx)
		#g.debug('self.__oldtxn: %r :: self.__txn: %r' % (self.__oldtxn, self.__txn))
		return self


	def __exit__(self, type, value, traceback):
		if self.__oldtxn is not self.__txn:
			if type is None: self._committxn()
			else:
				g.log_error('DBProxy.__exit__: type=%s, value=%s, traceback=%s' % (type, value, traceback))
				self._aborttxn()
			self.__txn = None
		self.__oldtxn = None


	# Transactions
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


	# We need to wrap the DB login method
	def login(self, username="anonymous", password="", host=None):

		try:
			host = host or self.__ctx.host
		except:
			host = None

		try:
			ctxid = self.__db.login(username=username, password=password, host=host, ctx=self.__ctx, txn=self.__txn)
			self._setContext(ctxid=ctxid, host=host)

		except:
			if self.__txn: self._aborttxn()
			raise

		return ctxid

	_login = login
	

	# Rebind a new Context
	def _setContext(self, ctxid=None, host=None):
		try:
			self.__ctx = self.__db._getcontext(ctxid=ctxid, host=host, txn=self.__txn)
			self.__ctx.setdb(db=self)

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
	def _register_publicmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		# g.log.msg('LOG_REGISTER', "REGISTERING PUBLICMETHOD (%s)" % name)
		cls.__publicmethods[name] = func

	@classmethod
	def _register_adminmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		# g.log.msg('LOG_REGISTER', "REGISTERING ADMINMETHOD (%s)" % name)
		cls.__adminmethods[name] = func

	@classmethod
	def _register_extmethod(cls, name, refcl):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		# g.log.msg('LOG_REGISTER', "REGISTERING EXTENSION (%s)" % name)
		cls.__extmethods[name] = refcl



	# Wrap DB calls to set Context and txn
	def _callmethod(self, method, args, kwargs):
		"""Call a method by name with args and kwargs (e.g. RPC access)"""
		
		args = list(args)
		method = method.split('.')
		func = getattr(self, method[0])
		result = None
		if len(method) > 1:
			result = getattr(MethodUtil(), method[1])(func, args, kwargs)
		else:
			result = func(*args, **kwargs)
		return result


	def _wrapmethod(self, func):
		@functools.wraps(func)
		def _inner(*args, **kwargs):
			with self:
				result = func(*args, **kwargs)
			return result
		return _inner


	def __getattr__(self, name):
		# print "__getattr__ %s"%name
		
		if name in self.__publicmethods:
			return self._publicmethod_wrap(name)
		
		elif name in self.__extmethods:
			return self._extmethod_wrap(name, ext=True)
		
		else:
			raise AttributeError('No such attribute %s of %r' % (name, self.__db))
	
	
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


	def _publicmethod_wrap(self, name, ext=False):		
		func = getattr(self.__db, name)
		kwargs = dict(ctx=self.__ctx, txn=self.__txn)
	
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			result = None
			commit = False
		
			ctx = self.__ctx
			kwargs['ctx'] = ctx
		
			txn = self.__txn
			if bool(txn) is False:
				txn = self.__db.newtxn()
				commit = True
			kwargs['txn'] = txn
		
			if ext:
				kwargs['db'] = self.__db
		
			try:
				# g.debug('func: %r, args: %r, kwargs: %r' % (func, args, kwargs))
				result = func(*args, **kwargs)
				
			except Exception, e:
				# traceback.print_exc(e)
				if commit is True:
					txn and self.__db.txnabort(ctx=ctx, txn=txn)
				raise
		
			else:
				if commit is True:
					txn and self.__db.txncommit(ctx=ctx, txn=txn)
		
			return result
		
		return wrapper
		
		






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
		
		
		