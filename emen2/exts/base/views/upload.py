# $Id$
import re
import os
import pickle
import traceback
import time
import random
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
	
	# def parse_content(self, request):		
	# 	# Look for filename; if PUT, add a reference to the request.content file handle.
	# 	postargs = {}
	# 
	# 	# Get the file name and data
	# 	if request.getHeader('X-Filename'):
	# 		postargs['filename'] = request.getHeader('X-Filename')
	# 
	# 	if request.method == "PUT":
	# 		postargs['infile'] = request.content
	# 
	# 	elif request.method == "POST":
	# 		request.content.seek(0)
	# 		content = request.content.read(1000)
	# 		b = re.compile("filename=\"(.+)\"")
	# 		try:
	# 			postargs['filename'] = b.findall(content)[0]
	# 		except:
	# 			pass
	# 
	# 	return postargs


	@View.add_matcher('^/upload/(?P<record>.+)/$')
	def main(self, filename, filedata, record=None, param='file_binary'):
		print "Uploading:", filename









# class UploadResource(emen2.web.resources.emen2resource.EMEN2Resource):
class UploadResource(object):

	resourcename = 'upload'

	##### EMEN2Resource interface #####

	def action(self, args=None, ctxid=None, host=None, db=None, request=None):
		infile = args.get('infile') or args.get('filedata')
		param = args.get('param', 'file_binary')
		filename = args.get('filename', '').split("/")[-1].split("\\")[-1]

		# ian: deprecate this feature...?
		if args.get('newrecord'):
			args['record'] = args['newrecord']

		if args.get('record'):
			try:
				record = jsonrpc.jsonutil.decode(urllib.unquote(args.get('record')))
			except ValueError, e:
				raise ValueError, "Invalid JSON record: %s"%e
		else:
			try:
				record = int(request.postpath[0])
			except (IndexError, TypeError, ValueError):
				# raise ValueError, "No Record name specified for upload"
				record = None

		# Action
		db._starttxn(write=True)
		with db._autoclean():
			db._setContext(ctxid, host)
			bdo = db.putbinary(None, filename=filename, record=record, infile=infile, param=param)

		# Redirect..
		headers = {}
		location = args.get("Location") or args.get("location")
		if location:
			headers['Location'] = location

		# emen2.web.thumbs.run_from_bdo(bdo, wait=False)
		# Return the BDO
		return jsonrpc.jsonutil.encode(bdo).encode("utf-8"), headers






__version__ = "$Revision$".split(":")[1][:-1].strip()
