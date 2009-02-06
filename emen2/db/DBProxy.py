# DBProxy.py 04/28/2005   Steven Ludtke
#
# This uses DBIsolator.py to provide access to the database without the possibility
# using low-level python programming to bypass security. It establishes a 
# 2-way pipe to the isolator, which performs all DB work

from os import popen2
from cPickle import load,dump
#from emen2.emen2config import *
#from g import *
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

import Database

#dbpath="/".join(__file__.split("/")[:-1])
dbpath=g.EMEN2ROOT
if len(dbpath)==0 : dbpath="."

class DBProxy:
	"""This class provides an interface to an EMEN2 database through a
DBIsolator process for security. Its interface is virtually identical
to the public Database interface, though it returns dictionaries and
lists rather than objects"""
	def __init__(self,path=g.EMEN2DBPATH):
		global dbpath
		self.iso=popen2('%s/DBIsolator.py %s 2>/tmp/dbug.txt'%(dbpath,path))	# returns a write,read file tuple
#		self.iso=popen2("%s/DBIsolator.py %s 2>/dev/null"%(dbpath,path))	# returns a write,read file tuple
#		self.log2=file("/tmp/dbug2.txt","a")
#		self.log2.write("---------------\n")
	
	def __del__(self):
		dump("EXIT",self.iso[0])
		self.iso[0].flush()
		self.iso=0
	
	def __getattr__(self,name):
		return lambda *x: self(name,*x)
		
	def __call__(self,*args, **kwargs):
		print kwargs
		for i in args:
			if isinstance(i,Database.Record) : i.localcpy=1
		print str(args)
#		self.log2.write("-> %s"%str(args))
		dump(args,self.iso[0])
		self.iso[0].flush()
		ret=load(self.iso[1])
		print str(ret)
#		self.log2.write("<- %s"%str(ret))
		return ret
