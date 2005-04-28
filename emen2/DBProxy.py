# DBProxy.py 04/28/2005   Steven Ludtke
#
# This uses DBIsolator.py to provide access to the database without the possibility
# using low-level python programming to bypass security. It establishes a 
# 2-way pipe to the isolator, which performs all DB work

from os import popen2
from cPickle import load,dump

class DBProxy():
	"""This class provides an interface to an EMEN2 database through a
DBIsolator process for security. Its interface is virtually identical
to the public Database interface, though it returns dictionaries and
lists rather than objects"""
	def __init__(self):
		self.iso=popen2("DBIsolator.py")	# returns a write,read file tuple
	
	def __del__(self):
		dump("EXIT",self.iso[0])
	
	def 
		