# DBProxy.py 04/28/2005   Steven Ludtke
#
# This uses DBIsolator.py to provide access to the database without the possibility
# using low-level python programming to bypass security. It establishes a 
# 2-way pipe to the isolator, which performs all DB work

from os import popen2
from cPickle import load,dump
from emen2.emen2config import *
import Database

#dbpath="/".join(__file__.split("/")[:-1])
dbpath=EMEN2ROOT
if len(dbpath)==0 : dbpath="."

class DBProxy:
	"""This class provides an interface to an EMEN2 database through a
DBIsolator process for security. Its interface is virtually identical
to the public Database interface, though it returns dictionaries and
lists rather than objects"""
	def __init__(self,path=EMEN2DBPATH):
		global dbpath
		self.iso=popen2("%s/DBIsolator.py %s 2>/tmp/dbug.txt"%(dbpath,path))	# returns a write,read file tuple
	
	def __del__(self):
		dump("EXIT",self.iso[0])
		self.iso[0].flush()
		self.iso=0
	
	def __getattr__(self,name) :
		return lambda *x: self(name,*x)
		
	def __call__(self,*args) :
		for i in args:
			if isinstance(i,Database.Record) : i.localcpy=1
		dump(args,self.iso[0])
		self.iso[0].flush()
		return load(self.iso[1])

