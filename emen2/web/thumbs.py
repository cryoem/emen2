#!/usr/bin/env python

# $Id$
import optparse
import os
import pickle
import sys
import tempfile
import gzip
import bz2
import random
import bz2
import subprocess
import json
from math import *

EXTS = set(["dm3", "tiff", "tif", "mrc", "jpg", "jpeg", "png", "gif"])
COMPRESS = set(["gz","bz2"])



def run_from_bdo(bdoo, wait=False):
	# Get config info to setup command
	import emen2.db.config
	g = emen2.db.config.g()
	python = g.EMAN2PYTHON
	e2t = emen2.db.config.get_filename('emen2','web/thumbs.py')
	tilepath = g.paths.TILEPATH


	filepath = bdoo.get('filepath')
	filename = bdoo.get('filename').split(".")

	if not os.access(filepath, os.F_OK):
		return

	compress = ""
	if filename[-1].lower() in ["bz2","gz"]:
		compress = filename[-1].lower()
		filename.pop()

	filetypes = ["jpg","jpeg","png","gif","dm3","mrc","tiff","tif"]
	filetype = filename[-1].lower()
	if filetype not in filetypes:
		return

	args = []
	if python:
		args.append(python)

	args.append(e2t)
	args.append("--outpath=%s/%s"%(tilepath, bdoo.get('name').replace(":",".")))
	args.append("--compress=%s"%compress)
	args.append("--type=%s"%filetype)
	args.append("--small")
	args.append("--thumb")
	args.append("--pspec")
	args.append("--convert=%s" % g.CONVERTPATH)
	args.append(filepath)

	print "running: %s"%args
	a = subprocess.Popen(args)
	if wait:
		a.wait()




def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] <tile file>

Operates on files containing sets of tiled JPEG images representing larger images. Used for
interactive web browsing."""

	parser = optparse.OptionParser(usage=usage)
	parser.add_option("--outpath", type="string", help="Output base: e.g: /data/file123 -> /data/file123.tile, /data/file123.small.jpg..")
	parser.add_option("--type", type="string", help="File type")
	parser.add_option("--compress", type="string", help="Compression type")
	parser.add_option("--convert", type="string", help="Location of ImageMagick convert")
	parser.add_option("--small", action="store_true", default=True, help="Build 512x512")
	parser.add_option("--thumb", action="store_true", default=True, help="Build 128x128")
	parser.add_option("--pspec",action="store_true", default=False, help="If set, then builds 1D and 2D power spectra for the images when building")
	parser.add_option("--tilesize", type="int", default=256, help="Build a new tile file from this image")

	(parsedoptions, args) = parser.parse_args()
	if len(args)<1:
		parser.error("Input file required")
	filepath = args[0]

	options = {}
	options['type'] = parsedoptions.type
	options['compress'] = parsedoptions.compress
	options['outpath'] = parsedoptions.outpath
	options['small'] = parsedoptions.small
	options['thumb'] = parsedoptions.thumb
	options['pspec'] = parsedoptions.pspec
	options['tilesize'] = parsedoptions.tilesize


	e = set(filepath.split("."))
	t = options.get('type')
	c = options.get('compress')

	if not t:
		t = (e & EXTS)
		if t: t = t.pop()
		else: t = None
		options['type'] = t

	if not c:
		if 'gz' in e or c == 'gz':
			options['compress'] = 'gz'
		if 'bz2' in e or c == 'bz2':
			options['compress'] = 'bz2'


	if options['type'] in ['dm3', 'mrc', 'tiff', 'tif']:
		processor = EMAN2Build(filepath, options=options)

	elif options['type'] in ['jpg','jpeg','png','gif']:
		processor = ImageBuild(filepath, options=options)

	else:
		parser.error("Unsupported file format")


	processor.build(convertutil=parsedoptions.convert)





class Builder(object):
	def __init__(self, filepath, options=None):
		self.options = options or {}
		self.filepath = filepath
		self.outpath = options.get('outpath') or self.filepath
		self.checkformat()


	def getoutfile(self, suffix):
		if not suffix:
			raise ValueError, "No suffix for out file"
		ret = "%s.%s"%(self.outpath, suffix)
		return ret


	def checkformat(self):
		pass


	def build(self, convertutil=None):
		pass




class ImageBuild(Builder):
	def checkformat(self):
		pass


	def _build_scale(self, img, size, outfile, convertutil="/usr/bin/convert"):
		# PIL...
		# im = self.Image.open(self.filepath)
		# im.thumbnail((size,size), self.Image.ANTIALIAS)
		# im.save(outfile, "JPEG")

		# ImageMagick...
		# convert -resize 128x128 -background white -gravity center -format jpg -quality 75 bdo:2010011400000  bdo:2010011400000.thumb.jpg
		args = [convertutil, "-resize %sx%s"%(size, size), "-gravity center", "-format jpg", "-quality 80"]
		if size <= 128:
			args.append("-extent %sx%s"%(size, size))

		args.append(self.filepath)
		args.append(outfile)
		print "running: %s"%args
		# join to a string, not sure why it doesn't work without it..
		a = subprocess.Popen(" ".join(args), shell=True)
		a.wait()

	def build(self, convertutil="/usr/bin/convert"):
		
		if not os.access(self.filepath, os.F_OK):
			return
		
		if self.options.get('small'):
			self._build_scale(None, 512, self.getoutfile("small.jpg"), convertutil=convertutil)

		if self.options.get('thumb'):
			self._build_scale(None, 128, self.getoutfile("thumb.jpg"), convertutil=convertutil)





class EMAN2Build(Builder):
	def checkformat(self):
		import matplotlib.backends.backend_agg
		import matplotlib.figure
		# import EMAN2
		#	raise ImportError, "EMAN2 needed to build thumbnails for this image type"
		self.EMAN2 = EMAN2
		self.matplotlib = matplotlib


	def tile_list(self, tilefile):
		"""tile_list(tilefile)
		Extract dictionary of tiles from a tilefile"""
		tf=file(tilefile,"r")
		td=pickle.load(tf)
		tf.close()
		return td



	def get_tile(self, tilefile,level,x,y):
		"""get_tile(tilefile,level,x,y)
		retrieve a tile from the file"""

		tf=file(tilefile,"r")

		td=pickle.load(tf)
		a=td[(level,x,y)]

		tf.seek(a[0],1)
		ret=tf.read(a[1])

		tf.close()
		return ret



	def build(self, convertutil=None):
		print "Building: %s"%(self.filepath)

		if not os.access(self.filepath, os.F_OK):
			return


		# setup temp dir
		self.tmpdir = tempfile.mkdtemp(prefix='emen2thumbs')
		workfile = self.filepath

		compress = self.options.get('compress')
		if compress == "gz":
			compress="gzip"
		elif compress == "bz2":
			compress = "bzip2"

		if compress:
			bn = os.path.basename(self.filepath)
			workfile = "%s.%s"%(bn, self.options.get('type'))
			workfile = os.path.join(self.tmpdir, workfile)
			print "Decompressing to %s"%workfile
			os.system("%s -d -c %s > %s"%(compress, self.filepath, workfile))

		
		if os.access(workfile, os.F_OK):	
			self._build_tiles(workfile=workfile)



	def _build_scale(self, img, size, outfile):
		print "Building scaled image: %s %s"%(size, outfile)
		img2 = img.copy()
		thumb_scale = img2.get_xsize()/float(size), img2.get_ysize()/float(size)
		sc = ceil(max(thumb_scale))
		img2.process_inplace("math.meanshrink", {"n":sc})
		rmin = img2.get_attr("mean") - img2.get_attr("sigma") * 3.0
		rmax = img2.get_attr("mean") + img2.get_attr("sigma") * 3.0
		img2.set_attr("render_min", rmin)
		img2.set_attr("render_max", rmax)
		img2.set_attr("jpeg_quality", 80)
		img2.write_image(outfile)



	def _build_tiles(self, workfile):
		# read the target and probe
		img = self.EMAN2.EMData()
		img.read_image(workfile)

		try:
			img.process_inplace("normalize")
		except:
			img.process_inplace("eman1.normalize")


		tilesize = self.options.get('tilesize')

		levels = ceil( log( max(img.get_xsize(), img.get_ysize()) / tilesize) / log(2.0) )

		# Step through shrink range creating tiles
		tile_dict={}
		pos = 0
		img2 = img.copy()
		xs, ys = img2.get_xsize(), img2.get_ysize()

		for l in range(int(levels)):
			rmin = img2.get_attr("mean") - img2.get_attr("sigma") * 3.0
			rmax = img2.get_attr("mean") + img2.get_attr("sigma") * 3.0

			for x in range(0, img2.get_xsize(), tilesize):
				for y in range(0, img2.get_ysize(), tilesize):
					# print x,y
					i = img2.get_clip(self.EMAN2.Region(x, y, tilesize, tilesize), fill=rmax)
					i.set_attr("render_min", rmin)
					i.set_attr("render_max", rmax)
					i.set_attr("jpeg_quality", 80)
					fsp = "%s/%d.%03d.%03d.jpg"%(self.tmpdir, l, x/tilesize, y/tilesize)
					i.write_image(fsp)
					sz = os.stat(fsp).st_size
					tile_dict[(l, x/tilesize, y/tilesize)] = (pos,sz)
					pos += sz

			img2.process_inplace("math.meanshrink",{"n":2})
			# img2.mean_shrink(2)


		# This will produce 2 power spectrum images in the tile file
		if self.options.get('pspec'):
			print "Building pspec"
			nx, ny = img.get_xsize() / 512, img.get_ysize() / 512
			a = self.EMAN2.EMData()
			a.set_size(512,512)

			if (ny>2 and nx>2):
				for y in range(1,ny-1):
					for x in range(1,nx-1):
						c = img.get_clip(self.EMAN2.Region(x*512,y*512,512,512))
						try:
							c.process_inplace("normalize")
						except:
							c.process_inplace("eman1.normalize")
						c.process_inplace("math.realtofft")
						c.process_inplace("math.squared")
						a += c

				a.set_value_at(256, 256 ,0, .01)
				a -= a.get_attr("minimum") - a.get_attr("sigma") * .01
				a.process_inplace("math.log")
				a.set_attr("render_min", a.get_attr("minimum") - a.get_attr("sigma") * .1)
				a.set_attr("render_max", a.get_attr("mean") + a.get_attr("sigma") * 4.0)
				print "Writing ", self.getoutfile("pspec.png")
				a.write_image(self.getoutfile("pspec.png"))

				x = range(0,255) # numpy.arange(0,255,1.0)
				y = a.calc_radial_dist(255,1,1,0) # radial power spectrum (log)

				f = open(self.getoutfile("radial.txt"), "w")
				json.dump(y,f)
				f.close()



		if self.options.get('small'):
			self._build_scale(img, 512, self.getoutfile("small.jpg"))

		if self.options.get('thumb'):
			self._build_scale(img, 128, self.getoutfile("thumb.jpg"))



		print "Saving to %s"%self.getoutfile("tile")
		tf = file(self.getoutfile("tile"),"w")
		pickle.dump(tile_dict, tf)

		for l in range(int(levels)):
			for x in range(0, xs, tilesize):
				for y in range(0, ys, tilesize):
					fsp = "%s/%d.%03d.%03d.jpg"%(self.tmpdir, l, x/tilesize, y/tilesize)
					a = file(fsp,"r")
					b = a.read()
					a.close()
					tf.write(b)
					os.remove(fsp)
			xs /= 2
			ys /= 2



		tf.close()

		if os.path.dirname(workfile) == self.tmpdir:
			os.remove(workfile)

		os.rmdir(self.tmpdir)



if __name__ == "__main__":
		main()

__version__ = "$Revision$".split(":")[1][:-1].strip()
