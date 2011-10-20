# $Id$
import re
import os
import pickle
import traceback
import time
import random
import collections
import cStringIO
import urllib
import jsonrpc.jsonutil

# emen2 imports
import emen2.web.resource
import emen2.web.thumbs
import emen2.db.config

from emen2.web.view import View






@View.register
class Upload(View):

	@View.add_matcher('^/upload/$', name='main')
	def main(self, *args, **kwargs):
		print "My files??"
		print self.request_files
		print "My args?"
		print args, kwargs
		
		
	@View.add_matcher('^/upload/(?P<record>.+)/$')
	def record(self, record=None, *args, **kwargs):
		print "Uploading to record %s"%record
		ret = []
		for f in self.request_files:
			print "...", f
			r = self.db.putbinary(None, infile=f.infile or f.filedata, filename=f.filename, record=record or f.record, param=f.param)		
			ret.append(r)
			


	@View.add_matcher('^/upload/create/$', name='create')
	def create(self, *args, **kwargs):
		print "My files??"
		print self.request_files
		print "My args?"
		print args, kwargs
		
		
	@View.add_matcher('^/upload/auto/$', name='create')
	def create(self, *args, **kwargs):
		print "Autocreating..."
		
		
		


__version__ = "$Revision$".split(":")[1][:-1].strip()
