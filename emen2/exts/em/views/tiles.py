# $Id$
import os
import pickle
import math
import json

import jsonrpc.jsonutil

import emen2.db.config
from emen2.web.view import View


# header[index][slices][tiles][(level, x, y)]


@View.register
class Preview(View):
	@View.add_matcher(r'^/preview/(?P<bid>.+)/(?P<mode>.+)/$')	
	def main(self, bid=None, mode='tiles', **kwargs):
		self.bid = bid
		if self.bid == None:
			return "No Binary ID supplied."

		# Make sure we can access bdo
		bdo = self.db.getbinary(self.bid, filt=False)

		self.filename = bdo.get('filename')
		self.mode = mode
		self.size = int(kwargs.get('size', 512))
		self.index = int(kwargs.get('index', 0))
		self.scale = int(kwargs.get('scale', 1))
		self.z = int(kwargs.get('z', 0))
		self.x = int(kwargs.get('x', 0))
		self.y = int(kwargs.get('y', 0))


	def get_data(self):
		previewpath = emen2.db.binary.Binary.parse(self.bid).get('previewpath')
		previewpath = '%s.eman2'%(previewpath)

		f = file(previewpath, "r")
		header = pickle.load(f)

		if self.mode == 'header':
			h = header[self.index]
			data = {
				'nx': h['nx'],
				'ny': h['ny'],
				'nz': h['nz'],
				'maxscale': 8,
				'filename': self.filename
			}
			f.close()
			return jsonrpc.jsonutil.encode(data)

		h = header[self.index]['slices'][self.z]
		key = self.size
		if self.mode == 'tiles':
			key = (self.scale, self.x, self.y)

		ret = h[self.mode][key]

		f.seek(ret[0], 1)
		data = f.read(ret[1])
		f.close()

		if ret[2] == 'jpg':
			self.set_header("Content-Type", "image/jpeg")
		elif ret[2] == 'png':
			self.set_header("Content-Type", "image/png")
		elif ret[2] == 'json':
			self.set_header("Content-Type", "application/json")

		return data
	




__version__ = "$Revision$".split(":")[1][:-1].strip()
