# $Id$
"""Proxy for accessing EMEN2 API methods

Classes:
	DBProxy
"""

from __future__ import with_statement

import os
import sys
import time
import collections
import traceback
import weakref
import functools
import inspect

# EMEN2 imports
from emen2.util import listops

# ian: The main DB class was cleaned up alot. I am going to merge the
# DBProxy functionality into it to remove one layer of abstraction.

##### Warning: This module is very sensitive to changes. Please test thoroughly before committing!! #####

def publicmethod(*args, **kwargs):
	"""Decorator for public admin API database method"""
	def _inner(func):
		# print "Registering ", func.func_name
		DBProxy._register_publicmethod(func, *args, **kwargs)
		return func
	return _inner



# class MethodUtil(object):
# 	allmethods = set(['doc'])
# 	def help(self, func, *args, **kwargs):
# 		return func.__doc__


strht = lambda s, c: s.partition(c)[::2]
def fb(): return 'hi'
def help(mt):
	def _inner(*a, **b):
		return dict(
			doc = getattr(mt, 'doc', None),
			methods = mt.children.keys()
		)
	return _inner


class MethodTree(object):
	'''Arranges the database methods into a tree so that they can be accessed as db.<a>.<b> (e.g. db.record.get)'''

	def __init__(self, func=None):
		self.func = func
		if func: self.doc = func.__doc__ or ''
		else: self.doc = ''
		self.children = {}
		self.aliases = {}

	def alias(self, original_name, new_name):
		'''define an alias for a certain method.

		:param new_name: the name to be replaced
		:param original_name: The replacement name
		'''

		if original_name in self.children:
			raise ValueError, "namespace conflict, cannot alias %r to %r" %(original_name, new_name)
		self.aliases[original_name] = new_name

	def get_alias(self, name):
		'''Check if the method sought has another name'''
		return self.aliases.get(name,name)

	def __repr__(self):
		return 'MethodTree: func: %r, children: %r' % (self.func, len(self.children.keys()))

	def __call__(self, *a, **kw):
		return self.func(*a, **kw)

	def __getattr__(self, name):
		if name.startswith('_'):
			return object.__getattribute__(self, name)
		name = name.replace('_', '.')
		return self.get_method(name)

	def add_method(self, name, func):
		'''Add a method to the tree

		Overview of the algorithm:
		--------------------------

		1. Split the method name at the first '.', the first part is the child to be found at present, the second is the 'tail'
		2. If the child does not exist, add it
		3. If tail is '', then insert 'func' as a method
		4. Otherwise, recurse on the tail

		:param name: the name of the method
		:param func: the function to be executed
		'''
		self._add_method(name, func)

	#NOTE: a is for debugging purposes, it can be removed
	def _add_method(self, name, func, a=1):
		head, _, tail = name.partition('.') # use partition and not split since it is guaranteed to return a 3-tuple

		self.children.setdefault(head, MethodTree())

		if tail == '':
			self.children[head].func = func
		else:
			self.children[head]._add_method(tail, func, a+1)

	def get_method(self, name):
		name = self.get_alias(name)
		return self._get_method(name)

	def _get_method(self, name):
		head, _, tail = name.partition('.')
		child = self.children.get(head)

		if child is None:
			if tail: raise AttributeError, "method %r not found"%name
			else:
				result = self
				if name == 'help':
					result = MethodTree(help(self))
		else:
			result = child._get_method(tail)

		return result






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



class DBProxy(object):
	"""A proxy that provides access to database public methods and handles low level details, such as Context and transactions.

	db = DBProxy()
	db._login(name, password)

	"""

	_publicmethods = {}
	mt = MethodTree()

	@classmethod
	def _allmethods(cls):
		return set(cls._publicmethods)

	def _get_publicmethods(self):
		result = {}
		for x in self._publicmethods:
			cur = result
			for y in x.split('.'):
				ncur = cur.get(y, {})
				if ncur is not cur: cur[y] = ncur
				cur = ncur
		return result


	def __init__(self, db=None, ctxid=None, host=None, ctx=None, txn=None):
		# it can cause circular imports if this is at the top level of the module
		import database

		self._txn = None
		self._is_bound = False

		if not db:
			db = database.DB()

		self._db = db
		self._ctx = ctx
		self._txn = txn


	##############
	# Transactions
	##############
	#: If true, close transaction on __exit__
	_txn_autoclean = False

	def _autoclean(self):
		"""set _txn_autoclean in order to allow the with statement to cleanup the txn"""
		self._txn_autoclean = True
		return self

	# Implements "with" interface
	def __enter__(self):
		if self._txn is None:
			self._starttxn()
			self._txn_autoclean = True
		return self


	def __exit__(self, type, value, traceback):
		if self._txn_autoclean and self._txn is not None:
			if type is None:
				self._committxn()
			else:
				self._aborttxn()
			self._txn_autoclean = False
			self._txn = None

	def _gettxn(self):
		return self._txn


	def _settxn(self, txn=None):
		self._txn = txn


	def _starttxn(self, write=False):
		self._txn = self._db.bdbs.txncheck(txn=self._txn, write=write)
		return self


	def _committxn(self):
		self._txn = self._db.bdbs.txncommit(txn=self._txn)


	def _aborttxn(self):
		self._txn = self._db.bdbs.txnabort(txn=self._txn)


	# Rebind a new Context
	def _setContext(self, ctxid=None, host=None):
		# try:
		self._ctx = self._db._getcontext(ctxid=ctxid, host=host, txn=self._txn)
		self._ctx.setdb(db=self)
		# except:
		# 	self._ctx = None
		# 	raise

		self._is_bound = True
		return self


	def _clearcontext(self):
		if self._is_bound:
			self._ctx = None


	def _getctx(self):
		return self._ctx


	@property
	def _bound():
		return self._is_bound


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
		# 	raise ValueError("""method %s already registered""" % name)
		setattr(func, 'apiname', apiname)
		setattr(func, 'write', write)
		setattr(func, 'admin', admin)
		setattr(func, 'ext', ext)

		cls._publicmethods[func.apiname] = func
		cls._publicmethods[func.func_name] = func

		cls.mt.add_method(apiname, func)
		cls.mt.add_method(func.func_name, func)


	def _checkwrite(self, method):
		return getattr(self.mt.get_method(method).func, "write", False)


	def _callmethod(self, method, args=(), kwargs={}):
		"""Call a method by name with args and kwargs (e.g. RPC access)"""
		#return getattr(self, method)(*args, **kwargs)
		m = self.mt.get_method(method).func
		if m is not None:
			return self._wrap(m)(*args, **kwargs)


	def __getattr__(self, name):
		if not name.startswith('_'):
			func = self._publicmethods.get(name)
		else: func = self.__getattribute__(name)
		if func: return self._wrap(func)
		return _Method(self, name)


	def _login(self, username, passwd, host=None):
		ctxid = self.login(username, passwd)
		self._setContext(ctxid, host)

	def _wrap(self, func):
		# print "going into wrapper for func: %s / %s"%(func.func_name, func.apiname)
		kwargs = dict(ctx=self._ctx, txn=self._txn)

		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			# self._db.periodic_operations.next()
			t = time.time()
			result = None
			commit = False

			# Remove these from the keyword arguments
			kwargs.pop('ctx', None)
			kwargs.pop('txn', None)

			# Pass the current bound Context
			ctx = self._ctx
			kwargs['ctx'] = ctx

			# If admin=True..
			if getattr(func, 'admin', False) and not ctx.checkadmin():
				raise Exception, "This method requires administrator level access."

			# Check there is an open transaction, and pass to method
			self._starttxn()
			kwargs['txn'] = self._txn
			try:
				ctx.setdb(self)
			except (AttributeError, NameError):
				pass

			# Pass the DB
			if getattr(func, 'ext', False):
				kwargs['db'] = self._db

			try:
				# result = func.execute(*args, **kwargs)
				result = func(self._db, *args, **kwargs)

			except Exception, e:
				# traceback.print_exc(e)
				if commit is True:
					txn and self._db.txnabort(ctx=ctx, txn=txn)
				raise

			else:
				if commit is True:
					txn and self._db.txncommit(ctx=ctx, txn=txn)

			# timer!
			# print "     <---------\t\t%10d ms: %s"%((time.time()-t)*1000, func.func_name)
			return result

		return wrapper


__version__ = "$Revision$".split(":")[1][:-1].strip()
