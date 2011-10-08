# $Id$
import os
import pickle
import math
import json

import jsonrpc.jsonutil

import emen2.db.config
import emen2.web.thumbs
from emen2.web.view import View


def get_tile(tilefile,level,x,y):
	"""get_tile(tilefile,level,x,y)
	retrieve a tile from the file"""


	tf=file(tilefile,"r")
	td=pickle.load(tf)

	try:
		a=td[(level,x,y)]
	except:
		raise KeyError,"Invalid Tile"
		
	tf.seek(a[0],1)
	ret = tf.read(a[1])
	tf.close()

	return ret




def get_tile_dim(tilefile):
	"""This will determine the number of tiles available in
	x and y at each level and return a list of (nx,ny) tuples"""

	tf=file(tilefile,"r")
	td=pickle.load(tf)
	tf.close()

	ret=[]
	for l in range(10):
		x,y= -1, -1
		for i in td:
			if i[0] == l:
				x,y = max(x,i[1]),max(y,i[2])
		if x==-1 and y==-1:
			break
		ret.append((x+1,y+1))

	return ret




@View.register
class Tiles(View):
	mimetype = "image/jpeg"

	@View.add_matcher(r'^/tiles/(?P<bid>.+)/image/$', view='Tiles', name='image')	
	def init(self, bid=None, **kwargs):
		self.bid=bid
		if self.bid == None:
			return "No Binary ID supplied."

		bdoo = self.db.getbinary(self.bid, filt=False)

		# transform TileImg params to old-style tile file
		self.level = int(kwargs.get('level', 0))
		self.x = int(kwargs.get('x', 0)) / (self.level * 256)
		self.y = int(kwargs.get('y', 0)) / (self.level * 256)
		self.level = math.log(self.level, 2)
		
				
	def get_data(self):
		tilepath = emen2.db.config.get('paths.TILEPATH')
		filepath = os.path.join(tilepath, self.bid.replace(":",".")+".tile")
		ret = get_tile(filepath, int(self.level), int(self.x), int(self.y))
		self.set_header("Content-Type", "image/jpeg")
		return ret





@View.register
class PSpec1D(View):
	mimetype = "image/jpeg"

	@View.add_matcher(r'^/tiles/(?P<bid>.+)/1d/$', view='Tiles', name='pspec1d')
	def init(self, bid=None, **kwargs):
		self.bid=bid
		if self.bid == None:
			return "No Binary ID supplied."

		self.bdoo = self.db.getbinary(self.bid, filt=False)
		self.angstroms_per_pixel = float(kwargs.get('angstroms_per_pixel', 1))
		self.tem_magnification_set = float(kwargs.get('tem_magnification_set', 0))
		self.length_camera = float(kwargs.get('length_camera', 0))
		self.binning = float(kwargs.get('binning', 1))
		self.pixel_pitch = float(kwargs.get('pixel_pitch', 0))
		self.rebuild = kwargs.get('rebuild')


	def get_data(self):
		tilepath = emen2.db.config.get('paths.TILEPATH')
		filepath = os.path.join(tilepath, self.bid.replace(":",".")+".radial.txt")

		# if not os.access(filepath, os.F_OK):
		# raise ValueError, "Could not access cached spatial frequency data"
		if self.rebuild or not os.access(filepath,os.R_OK):
			try:
				emen2.web.thumbs.run_from_bdo(self.bdoo, wait=True)
			except Exception, inst:
				raise ValueError, "Could not create tile"


		f = open(filepath, "r")
		y = json.load(f)
		f.close()
				
		dx = 1.0 / (2.0 * self.angstroms_per_pixel * (len(y)+1))
		x = [dx*(i+1) for i in range(len(y))]
		
		q = self.db.plot(x, y, plotmode="xy", xlabel="Spatial Freq. (1/A); A/pix set to %s"%self.angstroms_per_pixel, ylabel="Log Intensity (10^x)")
		f = open(q['plots']['png'], "r")
		ret = f.read()
		f.close()

		self.set_header("Content-Type", "image/png")
		return ret



@View.register
class TilesCheck(View):

	@View.add_matcher(r'^/tiles/(?P<bid>.+)/check/$', view='Tiles', name='check')	
	def init(self, bid=None):
		self.bid = bid
		self.rebuild = False
		View.init(self)

	def get_data(self):	
		ret=()
		bdoo = self.db.getbinary(self.bid, filt=False)

		bname = bdoo.get('filename')
		ipath = bdoo.get('filepath')
		bdocounter = bdoo.get('name')
		tilepath = emen2.db.config.get('paths.TILEPATH')
		filepath = os.path.join(tilepath, self.bid.replace(":",".")+".tile")

		if self.rebuild or not os.access(filepath,os.R_OK):
			try:
				emen2.web.thumbs.run_from_bdo(bdoo, wait=True)
			except Exception, inst:
				raise ValueError, "Could not create tile"


		dims = get_tile_dim(filepath)
		dimsx = [i[0] for i in dims]
		dimsy = [i[1] for i in dims]
			
		ret = {}
		ret['width'] = max(dimsx) * 256
		ret['height'] = max(dimsy) * 256
		ret['maxscale'] = math.pow(2, len(dimsx)-1)
		ret['filename'] = bdoo.get('filename')

		return jsonrpc.jsonutil.encode(ret)




@View.register
class TilesCreate(View):

	@View.add_matcher(r'^/tiles/(?P<bid>.+)/create/$', view='Tiles', name='create')
	def init(self,bid=None):
		self.bid=bid

	def get_data(self):
		ret = ()
		bdoo = self.db.getbinary(self.bid, filt=False)
		bname = bdoo.get('filename')
		ipath = bdoo.get('filepath')
		bdocounter = bdoo.get('name')


		if not os.access(filepath,os.R_OK):
			raise Exception,"Unable to create tile"
			#return (-1,-1,bid)
		else:
			dims=get_tile_dim(filepath)
			dimsx=[i[0] for i in dims]
			dimsy=[i[1] for i in dims]
			ret=(dimsx,dimsy,self.bid)

		return jsonrpc.jsonutil.encode(ret)


__version__ = "$Revision$".split(":")[1][:-1].strip()
