# $Id$
'''File handlers

'''

import time
import re
import traceback
import math
import os

# For file writing
import shutil
import hashlib
import cStringIO
import tempfile

# EMEN2 imports
import emen2.db.config
import emen2.db.exceptions


def sign(a):
	if a>0: return 1
	return -1


def eman2_thumbnail(f):
	pass
	

def emdata_rename(header):
	'''Convert EMData attributes to EMEN2 parameter names'''
	ret = {}
	mrclabels = []
	for k,v in header.items():
		if k.startswith('MRC.label'):
			mrclabels.append(v)
			continue
		k = k.replace('.','_').lower()
		ret[k] = v

	if mrclabels:
		ret['mrc_label'] = mrclabels
		
	return ret
		

def rename_emdata(header):
	'''Convert EMEN2 parameter names to EMData attributes'''
	prefixes = ['mrc', 'dm3', 'tiff', 'imagic', 'spider']
	ret = {}
	for k,v in header.items():
		pfx, _, sfx = k.partition('_')
		if pfx in prefixes:
			k = '%s.%s'%(pfx.upper(), sfx)
		ret[k] = v
	return ret



def filter_ext(files, exts):
	ret = []
	for f in files:
		b, _, ext = f.filename.rpartition(".")
		print b, ext
		if ext.lower() in exts:
			ret.append(f)
	return ret
		
		

##### Managed file handler. See emen2.db.database.Binary for more details. #####

class EMEN2File(object):
	'''EMEN2 managed file. This class is used for importing and reading files managed by EMEN2 Binaries.
	
	The original name of the file is self.filename. Input sources can be a added in the constructor, and
	may be a string of data (filedata), a file-like object supporting read() (fileobj), or a 
	filename on disk (infile, currently disabled). Generally, consider the data sources to be READ ONLY.
	
	The writetmp() method will return an on-disk filename that can be used for operations that required
	a named file (e.g. EMAN2.) If the input source is filedata or fileobj, it will write out to a temporary
	file in the normal temp file storage area. The cleanup() method will remove any temporary files.
	
	The writebinary() method will write out the file to a temporary storage location in the correct
	EMEN2 Binary storage area, and will return (path, filesize, md5). The tmp file will have a '.upload'
	extension. If the Binary commit is successful, you can then use a simple, atomic file rename 
	operation to move it into place. If not, it can be removed immediately, or a script can be used to 
	clean out all '.upload' files.
	'''
	
	def __init__(self, filename, filedata=None, fileobj=None, param='file_binary'):
		self.filename = filename
		self.filedata = filedata
		self.fileobj = fileobj
		self.infile = None
		self.param = param
		self.readonly = True
		self.tmp = None

	def __repr__(self):
		# For debugging.
		mode = 'infile'
		if self.filedata:
			mode = 'filedata'
		elif self.fileobj:
			mode = 'fileobj'
		print '<EMEN2File %s (%s)>'%(self.filename, mode)
		
	def open(self):
		'''Open the file'''
		# Open the filedata
		readfile = None
		if self.filedata:
			# This is fine; strings are immutable, cStringIO will reuse the buffer
			readfile = cStringIO.StringIO(self.filedata)
		elif self.fileobj:
			# ... use the fileobj
			self.fileobj.seek(0)
			readfile = self.fileobj
		#elif self.infile:
		#	# ... or open the file
		#	readfile = open(self.infile, 'rb')
		else:
			raise IOError, "No file given or don't know how to read file.."

	def writetmp(self, path=None, suffix=None):
		'''Write to temporary storage and calculate size / md5
		:return: Temporary file path, the file size, and an md5 digest.		
		'''

		infile = self.open()
		
		# Make a temporary file
		args = {}
		if suffix: args['suffix'] = suffix
		if path: args['dir'] = path
		(fd, tmpfile) = tempfile.mkstemp(**args)

		# Copy to the output file, updating md5 and size
		with os.fdopen(fd, "w+b") as f:
			for line in infile:
				f.write(line)
				m.update(line)
				filesize += len(line)

		if self.infile:
			infile.close()

		md5sum = m.hexdigest()
		# print "Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfilepath, filesize, md5sum)
		emen2.db.log.info("Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfile, filesize, md5sum))

		return tmpfilepath, filesize, md5sum

	# ian: todo: better job at cleaning up broken files..
	def writebinary(self):
		"""Write filedata out to a temporary file in the EMEN2 Binary storage area.
		:return: Temporary file path, the file size, and an md5 digest.		
		"""
		
		# Get the basepath for the current storage area
		dkey = emen2.db.binary.Binary.parse('')

		# Make the directory
		try:
			os.makedirs(dkey["basepath"])
		except OSError:
			pass
			
		return self.writetmp(suffix='.upload', path=dkey['basepath'])	

	def rename(self, newname):
		pass

	def cleanup(self):
		pass
		
		

##### Generic file handlers #####

class Handler(object):
	rectypes = []
	extensions = []

	def __init__(self, files=None):
		self.files = files

	def extract(self):
		return {}

	def thumbnail(self, f):
		pass



##### Specific file type handlers #####
# In the future, these may be moved into 
#	extension modules and registered with the parent class

class movie(Handler):
	extensions = ['avi', 'flv', 'mpg', 'mp4', 'mov']


class image(Handler):
	extensions = ['jpg', 'jpeg', 'png', 'gif', 'tif', 'tiff', 'bmp', 'crw', 'nef', 'mng']


class dicom(Handler):
	extensions = ['dcm', 'dicom']


class pdf(Handler):
	extensions = ['pdf']



##### Cryo-EM handlers #####

class ccd(Handler):
	extensions = ['dm3', 'tif', 'tiff', 'mrc']

	def extract(self):
		f = filter_ext(self.files, self.extensions)
		if len(f) != 1:
			raise ValueError, "Needs exactly one CCD frame"
		f = f[0]

		filename = f.writetmp()

		# Get the basic header from EMAN2
		img = EMAN2.EMData()
		img.read_image(filename, 0, True)
		header = img.get_attr_dict()

		# Convert
		return emdata_rename(header)

	def thumbnail(self, f):
		pass


class stack(Handler):
	extensions = ['st']

	# IMOD SerialEM format
	# http://bio3d.colorado.edu/imod/doc/guide.html	

	# Start at a 92 byte offset (standard MRC header attributes)
	# Then read in the following SerialEM Headers.
	# [target parameter, C struct type, default value]
	header_labels = [
		# Number of bytes in extended header
		['serialem_extheadersize', 'i', 0],
		# Creator ID, creatid
		['serialem_creatid', 'h', 0],
		# 30 bytes of unused data
		[None, '30s', ''],
		## Number of bytes per section (SerialEM format) of extended header
		['serialem_bytespersection', 'h', 0],
		# Flags for which types of short data (SerialEM format), nreal. (See extheader_flags)
		['serialem_extheaderflags', 'h', 0],
		# 28 bytes of unused data
		[None, '28s', ''],
		# Additional SerialEM attributes
		['serialem_idtype', 'h', 0],
		['serialem_lens', 'h', 0],
		['serialem_nd1', 'h', 0],
		['serialem_nd2', 'h', 0],
		['serialem_vd1', 'h', 0],
		['serialem_vd2', 'h', 0],
		['serialem_tiltangles_orig', 'fff', [0.0, 0.0, 0.0]],
		['serialem_tiltangles_current', 'fff', [0.0, 0.0, 0.0]],
		['serialem_xorg', 'f', 0.0],
		['serialem_yorg', 'f', 0.0],
		['serialem_zorg', 'f', 0.0],
		['serialem_cmap', '4s', '']
	]

	# The SerialEM extended header is a mask
	# Compare with the following keys to find the attributes
	extheader_flags = {
		1: {'pack': 'h',
			'load': lambda x:[x[0] / 100.0],
			'dump': lambda x:[x[0] * 100],
			'dest':  ['serialem_tilt'],
			'also': ['specimen_tilt']},

		2: {'pack': 'hhh',
			'load': lambda x:[x],
			'dump': lambda x:[x],
			'dest': ['serialem_montage']},

		4: {'pack': 'hh',
			'load': lambda x:[x[0] / 25.0 , x[1] / 25.0],
			'dump': lambda x:[x[0] * 25   , x[1] * 25],
			'dest': ['serialem_stage_x', 'serialem_stage_y'],
			'also': ['position_stage_x', 'position_stage_y']},

		8: {'pack': 'h',
			'load': lambda x:[x[0] / 10.0],
			'dump': lambda x:[x[0] * 10],
			'dest': ['serialem_magnification'],
			'also': ['tem_magnification_set']},

		16: {'pack': 'h',
			'load': lambda x:[x[0] / 25000.0],
			'dump': lambda x:[x[0] * 25000],
			'dest': ['serialem_intensity']},

		32: {'pack': 'hh',
			'load': lambda x:[sign(x[0])*(math.fabs(x[0])*256+(math.fabs(x[1])%256))*2**(sign(x[1])*(int(math.fabs(x[1]))/256))],
			'dump': lambda x:[0,0],
			'dest': ['serialem_dose']}
	}

	def extract(self):		
		f = filter_ext(self.files, self.extensions)
		if len(f) != 1:
			raise ValueError, "Needs exactly one SerialEM stack"
		f = f[0]

		filename = f.writetmp()
		self.filename = filename

		# Get the basic header from EMAN2
		img = EMAN2.EMData()
		img.read_image(filename, 0, True)
		self.h = img.get_attr_dict()
		self.get_header()

		# Read the SerialEM header and extended header
		# header["serialem_maxangle"] = max(tilts)
		# header["serialem_minangle"] = min(tilts)

		# Convert
		return emdata_rename(self.h)


	##### Read SerialEM extended header #####

	def get_header(self):
		"""Read an IMOD/SerialEM/MRC stack header"""
		f = open(self.filename,"rb")

		hdata = f.read(1024)

		h = self._get_header(hdata)
		self.h.update(h)

		size = self.h["serialem_extheadersize"]
		nz = self.h['nz']
		flags = self.h['serialem_extheaderflags']

		ehdata = f.read(size)		
		extheader = self._get_extheader(ehdata=ehdata, nz=nz, flags=flags)
		self.h['slices'] = extheader
		f.close()

	def _get_header(self, hdata, offset=92):
		"""Extract data from header string (1024 bytes) and process"""
		d={}
		for dest, format, default in self.header_labels:
			size = struct.calcsize(format)
			value = struct.unpack(format, hdata[offset:offset+size])
			if dest == None:
				pass
			elif len(value) == 1:
				d[dest] = value[0]
			else:
				d[dest] = value
			offset += size
		return d

	def _get_extheader(self, ehdata, nz, flags):
		"""Process extended header"""

		ed = []
		offset = 0

		# Get the extended header attributes
		keys = self._extheader_getkeys(flags)

		# For each slice..
		for i in range(0, nz):
			sslice = {}

			# Process each extended header attribute
			for key in keys:
				# Get the flags and calculate the size
				parser = self.extheader_flags.get(key)
				size = struct.calcsize(parser['pack'])

				# Parse the section
				# print "Consuming %s bytes (%s:%s) for %s"%(size, i+offset, i+offset+size, parser['dest'])
				value = struct.unpack(parser['pack'], ehdata[offset: offset+size])

				# Process the packed value
				value = parser['load'](value)

				# Update the slice
				for dest,v in zip(parser.get('dest', []), value):
					sslice[dest] = v
				for dest,v in zip(parser.get('also', []), value):
					sslice[dest] = v

				# Read the next section
				offset += size

			ed.append(sslice)

		return ed

	def _extheader_getkeys(self, flags):
		keys = []
		for i in sorted(self.extheader_flags.keys()):
			if flags & i:
				keys.append(i)
		return keys




class ddd(Handler):
	pass
	# ddd_mapping = {
	# 	'Binning X': 'binning_x',
	# 	'Binning Y': 'binning_y',
	# 	'Camera Position': 'camera_position',
	# 	'Dark Correction': 'ddd_dark_correction',
	# 	'Dark Frame Status': 'ddd_dark_frame_status',
	# 	'Data Output Mode': 'ddd_data_output_mode',
	# 	'Exposure Mode': 'ddd_exposure_mode',
	# 	'FPGA Version': 'ddd_fpga_version',
	# 	'Faraday Plate Peak Reading During Last Exposure': 'faraday_plate_peak',
	# 	'Gain Correction': 'ddd_gain_correction',
	# 	'Gain Frame Status': 'ddd_gain_frame_status',
	# 	'Hardware Binning X': 'binning_hardware_x',
	# 	'Hardware Binning Y': 'binning_hardware_y',
	# 	'Last Dark Frame Dataset': 'ddd_last_dark_frame_dataset',
	# 	'Last Gain Frame Dataset': 'ddd_last_gain_frame_dataset',
	# 	'Preexposure Time in Seconds': 'time_preexposure',
	# 	'ROI Offset H': 'roi_offset_h',
	# 	'ROI Offset W': 'roi_offset_w',
	# 	'ROI Offset X': 'roi_offset_x',
	# 	'ROI Offset Y': 'roi_offset_y',
	# 	'Raw Frames Filename Suffix': 'ddd_raw_frame_suffix',
	# 	'Raw Frames Type': 'ddd_raw_frame_type',
	# 	'Save Raw Frames': 'ddd_raw_frame_save',
	# 	'Save Summed Image': 'ddd_raw_frame_save_summed',
	# 	'Screen Position': 'screen_position',
	# 	'Sensor Coarse Gain': 'ddd_sensor_coarse_gain',
	# 	'Sensor Offset': 'ddd_sensor_offset',
	# 	'Sensor Output Mode': 'ddd_sensor_output_mode',
	# 	'Temperature Cold Finger (Celsius)': 'ddd_temperature_cold_finger',
	# 	'Temperature Control': 'ddd_temperature_control',
	# 	'Temperature Control Mode': 'ddd_temperature_control_mode',
	# 	'Temperature Detector (Celsius)': 'ddd_temperature_detector',
	# 	'Temperature TEC Current (Ampere)': 'ddd_temperature_tec_current',
	# 	'Temperature Water Line (Celsius)': 'ddd_temperature_water_line',
	# 	'Vacuum Level': 'vacuum_level'
	# }
	# 
	# def load_ddd_metadata(self):
	# 	foundfiles = []
	# 	ret = {}
	# 	infoname = os.path.join(os.path.dirname(self.filename), 'info.txt')
	# 	print "Checking:", infoname
	# 	if os.path.exists(infoname):
	# 		f = open(infoname)
	# 		data = f.readlines()
	# 		f.close()
	# 		for line in data:
	# 			param, _, value = line.strip().partition("=")
	# 			mapparam = self.ddd_mapping.get(param)
	# 			if mapparam:
	# 				# print 'param %s -> %s: %s'%(param, mapparam, value)
	# 				ret[mapparam] = value
	# 
	# 		foundfiles.append(infoname)			
	# 	return ret, foundfiles	
	# 
	# def get_upload_items(self):
	# 	ddd_params, foundfiles = self.load_ddd_metadata()
	# 	newrecord = {}
	# 	newrecord["name"] = -100
	# 	newrecord["rectype"] = "ddd"
	# 	newrecord.update(self.applyparams)
	# 	newrecord.update(ddd_params)
	# 	newrecord["parents"] = [self.name]
	# 	dname = os.path.split(os.path.dirname(self.filename))[-1]
	# 	fname = os.path.basename(self.filename)
	# 	uploadname = '%s-%s'%(dname, fname)
	# 	newrecord['id_ccd_frame'] = uploadname
	# 
	# 	files = [emdash.transport.UploadTransport(name=-100, uploadname=uploadname, filename=self.filename, param='file_binary_image')]
	# 	files[0].newrecord = newrecord		
	# 
	# 	for i in foundfiles:
	# 		files.append(emdash.transport.UploadTransport(name=-100, filename=i, uploadname='%s-%s'%(dname, os.path.basename(i)), compress=False))
	# 
	# 	return files
	# 	





class ccd_jadas(Handler):
	"""Creates a placeholder for a scan to be uploaded in the future"""
	pass
	# rectype = 'ccd_jadas'
	# 
	# def get_upload_items(self):
	# 	# This is run for a .tif file produced by JADAS. Find the associated .xml files, load them, map as many
	# 	# parameters as possible, and attach the raw xml file.
	# 	jadas_params, foundfiles = self.load_jadas_xml()
	# 	
	# 	newrecord = {}
	# 	newrecord["name"] = -100
	# 	newrecord["rectype"] = "ccd_jadas"
	# 	newrecord["id_micrograph"] = os.path.basename(self.filename)
	# 	newrecord.update(self.applyparams)
	# 	newrecord.update(jadas_params)
	# 	newrecord["parents"] = [self.name]
	# 	
	# 	files = [emdash.transport.UploadTransport(name=-100, filename=self.filename, param='file_binary_image')]
	# 	files[0].newrecord = newrecord
	# 	
	# 	for i in foundfiles:
	# 		files.append(emdash.transport.UploadTransport(name=-100, filename=i, compress=False))
	# 			
	# 	return files
	# 
	# 
	# def load_jadas_xml(self):
	# 	# find related XML files, according to JADAS naming conventions
	# 	# take off the .tif, because the xml could be either file.tif_metadata.xml or file_metadata.xml
	# 	if not ET:
	# 		raise ImportError, "The ElementTree package (xml.etree.ElementTree) is required"
	# 		
	# 	foundfiles = []
	# 	ret = {}		
	# 	for xmlfile in glob.glob('%s_*.xml'%self.filename) + glob.glob('%s_*.xml'%self.filename.replace('.tif','')):
	# 		print "Attempting to load ", xmlfile
	# 		try:
	# 			e = ET.parse(xmlfile)
	# 			root = e.getroot()
	# 			# There should be a loader for each root tag type, e.g. TemParameter -> map_jadas_TemParameter
	# 			loader = getattr(self, 'map_jadas_%s'%root.tag, None)
	# 			if loader:
	# 				ret.update(loader(root))
	# 				foundfiles.append(xmlfile)
	# 		except Exception, e:
	# 			print "Could not load %s: %s"%(xmlfile, e)
	# 
	# 	return ret, foundfiles
	# 
	# 
	# 
	# def map_jadas_TemParameter(self, root):
	# 	"""One of these long, ugly, metadata-mapping methods"""
	# 	ret = {}
	# 	# Defocus
	# 	ret['defocus_absdac'] = root.find('Defocus/defocus').get('absDac')
	# 	ret['defocus_realphysval'] = root.find('Defocus/defocus').get('relPhisVal')
	# 	ret['intendeddefocus_valinnm'] = root.find('Defocus/intendedDefocus').get('valInNm')
	# 	d = root.find('Defocus/intendedDefocus').get('valInNm')
	# 	if d != None:
	# 		d = float(d) / 1000.0
	# 		ret['ctf_defocus_set'] = d
	# 
	# 	# Eos
	# 	ret['eos_brightdarkmode'] = root.find('Eos/eos').get('brightDarkMode')
	# 	ret['eos_darklevel'] = root.find('Eos/eos').get('darkLevel')
	# 	ret['eos_stiglevel'] = root.find('Eos/eos').get('stigLevel')
	# 	ret['eos_temasidmode'] = root.find('Eos/eos').get('temAsidMode')
	# 	ret['eos_htlevel'] = root.find('Eos/eos').get('htLevel')
	# 	ret['eos_imagingmode'] = root.find('Eos/eos').get('imagingMode')
	# 	ret['eos_magcamindex'] = root.find('Eos/eos').get('magCamIndex')
	# 	ret['eos_spectrummode'] = root.find('Eos/eos').get('spectrumMode')
	# 	ret['eos_illuminationmode'] = root.find('Eos/eos').get('illuminationMode')
	# 	ret['eos_spot'] = root.find('Eos/eos').get('spot')
	# 	ret['eos_alpha'] = root.find('Eos/eos').get('alpha')
	# 
	# 	# Lens
	# 	ret['lens_cl1dac'] = root.find('Lens/lens').get('cl1Dac')
	# 	ret['lens_cl2dac'] = root.find('Lens/lens').get('cl2Dac')
	# 	ret['lens_cl3dac'] = root.find('Lens/lens').get('cl3Dac')
	# 	ret['lens_cmdac'] = root.find('Lens/lens').get('cmDac')
	# 	ret['lens_il1dac'] = root.find('Lens/lens').get('il1Dac')
	# 	ret['lens_il2dac'] = root.find('Lens/lens').get('il2Dac')
	# 	ret['lens_il3dac'] = root.find('Lens/lens').get('il3Dac')
	# 	ret['lens_il4dac'] = root.find('Lens/lens').get('il4Dac')
	# 	ret['lens_pl1dac'] = root.find('Lens/lens').get('pl1Dac')
	# 	ret['lens_pl2dac'] = root.find('Lens/lens').get('pl2Dac')
	# 	ret['lens_pl3dac'] = root.find('Lens/lens').get('pl3Dac')
	# 	
	# 	# Def
	# 	ret['def_gunshiftx'] = root.find('Def/def').get('gunShiftX')
	# 	ret['def_gunshifty'] = root.find('Def/def').get('gunShiftY')
	# 	ret['def_guntiltx'] = root.find('Def/def').get('gunTiltX')
	# 	ret['def_guntilty'] = root.find('Def/def').get('gunTiltY')
	# 	ret['def_beamshiftx'] = root.find('Def/def').get('beamShiftX')
	# 	ret['def_beamshifty'] = root.find('Def/def').get('beamShiftY')
	# 	ret['def_beamtiltx'] = root.find('Def/def').get('beamTiltX')
	# 	ret['def_beamtilty'] = root.find('Def/def').get('beamTiltY')			
	# 	ret['def_clstigx'] = root.find('Def/def').get('clStigX')
	# 	ret['def_clstigy'] = root.find('Def/def').get('clStigY')
	# 	ret['def_olstigx'] = root.find('Def/def').get('olStigX')
	# 	ret['def_olstigy'] = root.find('Def/def').get('olStigY')
	# 	ret['def_ilstigx'] = root.find('Def/def').get('ilStigX')
	# 	ret['def_ilstigy'] = root.find('Def/def').get('ilStigY')
	# 	ret['def_imageshiftx'] = root.find('Def/def').get('imageShiftX')
	# 	ret['def_imageshifty'] = root.find('Def/def').get('imageShiftY')
	# 	ret['def_plax'] = root.find('Def/def').get('plaX')
	# 	ret['def_play'] = root.find('Def/def').get('plaY')
	# 	
	# 	# HT
	# 	ret['ht_ht'] = root.find('HT/ht').get('ht')
	# 	ret['ht_energyshift'] = root.find('HT/ht').get('energyShift')
	# 	
	# 	# MDS
	# 	ret['mds_mdsmode'] = root.find('MDS/mds').get('mdsMode')
	# 	ret['mds_blankingdef'] = root.find('MDS/mds').get('blankingDef')
	# 	ret['mds_defx'] = root.find('MDS/mds').get('defX')
	# 	ret['mds_defy'] = root.find('MDS/mds').get('defY')
	# 	ret['mds_blankingtype'] = root.find('MDS/mds').get('blankingType')
	# 	ret['mds_blankingtime'] = root.find('MDS/mds').get('blankingTime')
	# 	ret['mds_shutterdelay'] = root.find('MDS/mds').get('shutterDelay')
	# 	
	# 	# Photo
	# 	ret['photo_exposuremode'] = root.find('PHOTO/photo').get('exposureMode')
	# 	ret['photo_manualexptime'] = root.find('PHOTO/photo').get('manualExpTime')
	# 	ret['photo_filmtext'] = root.find('PHOTO/photo').get('filmText')
	# 	ret['photo_filmnumber'] = root.find('PHOTO/photo').get('filmNumber')
	# 	
	# 	# GonioPos
	# 	ret['goniopos_x'] = root.find('GonioPos/gonioPos').get('x')
	# 	ret['goniopos_y'] = root.find('GonioPos/gonioPos').get('y')
	# 	ret['goniopos_z'] = root.find('GonioPos/gonioPos').get('z')
	# 	ret['goniopos_tiltx'] = root.find('GonioPos/gonioPos').get('tiltX')
	# 	ret['goniopos_rotortilty'] = root.find('GonioPos/gonioPos').get('rotOrTiltY')
	# 
	# 	return ret
	# 	
	# 	
	# 	
	# def map_jadas_DigitalCameraParameter(self, root):
	# 	attrmap = {
	# 		'CameraName': 'ccd_id',
	# 		'AreaTop': 'digicamprm_areatop',
	# 		'AreaBottom': 'digicamprm_areabottom',
	# 		'AreaLeft': 'digicamprm_arealeft',
	# 		'AreaRight': 'digicamprm_arearight',
	# 		'Exposure': 'time_exposure_tem',
	# 		'Binning': 'binning',
	# 		'PreIrradiation': 'digicamcond_preirradiation',
	# 		'BlankingTime': 'digicamcond_blankingtime',
	# 		'BlankBeam': 'digicamcond_blankbeam',
	# 		'CloseScreen': 'digicamcond_closescreen',
	# 		'DataFormat': 'digicamcond_dataformat'		
	# 	}
	# 
	# 	ret = {}
	# 	for i in root.findall('*/tagCamPrm'):
	# 		param = attrmap.get(i.get('tagAttrName'))
	# 		value = i.get('tagAttrVal')
	# 		if param != None and value != None:
	# 			ret[param] = value		
	# 
	# 	return ret
	# 	
	# 	
	# 	
	# def map_jadas_IntensityBasedHoleSelection(self, root):
	# 	ret = {}
	# 	return ret
	# 	








class scan(Handler):
	pass
	# rectype = 'scan'
	# 
	# request_params = [
	# 	'scanner_film',
	# 	'scanner_cartridge',
	# 	'scan_average',
	# 	'nikon_gain',
	# 	'scan_step',
	# 	'angstroms_per_pixel'
	# 	]
	# 
	# 
	# def get_upload_items(self):
	# 	print "Checking for existing micrograph..."
	# 	idmap = collections.defaultdict(set)
	# 	mc = self.db.getchildren(self.name, 1, "micrograph")
	# 	mc = self.db.getrecord(mc)
	# 	for rec in mc:
	# 		i = rec.get('id_micrograph', '').strip().lower()
	# 		idmap[i].add(rec.get('name'))
	# 
	# 	outfile = self.filename
	# 
	# 	# This is an ugly hack until I think of a better way
	# 	opts = {}
	# 	try:
	# 		# tif2mrc, bin, invert, odconversion
	# 		for i in ['tif2mrc', 'bin', 'invert', 'odconversion']:
	# 			opts[i] = emdash.config.get(i)
	# 			# getattr(emdash.config, i, None)
	# 		print "Using options for ScanHandler:", opts
	# 	except:
	# 		pass
	# 
	# 	if opts.get('tif2mrc'):
	# 		outfile = outfile.replace('.tif', '.mrc')
	# 		args = []
	# 		# if python:
	# 		# 	args.append(python)
	# 		args.append('nikontiff2mrc.py')
	# 		if opts.get('bin') != None:
	# 			args.append('--bin=%s'%opts.get('bin'))
	# 		if opts.get('invert') != None:
	# 			args.append('--invert=%s'%opts.get('invert'))
	# 		if opts.get('odconversion') != None:
	# 			args.append('--ODconversion=%s'%opts.get('odconversion'))
	# 
	# 		args.append(self.filename)
	# 		args.append(outfile)
	# 		
	# 		print "running: %s"%args
	# 		a = subprocess.Popen(args)
	# 		a.wait()
	# 
	# 	# Try to find matches between the current filename and items in the imaging session
	# 	match = os.path.basename(outfile.split(".")[0].strip().lower())
	# 	matches = idmap[match]
	# 
	# 	if len(idmap[match]) == 0:
	# 		print "Could not find micrograph for %s -- creating new micrograph."%match
	# 
	# 		mrec = {}
	# 		mrec["name"] = -1
	# 		mrec["rectype"] = "micrograph"
	# 		mrec["parents"] = [self.name]
	# 		mrec["id_micrograph"] = match
	# 
	# 		newrecord = {}
	# 		newrecord["name"] = -2
	# 		newrecord["rectype"] = 'scan'
	# 		newrecord["parents"] = [-1]
	# 		newrecord.update(self.applyparams)
	# 
	# 		m = emdash.transport.NewRecordTransport(newrecord=mrec)
	# 		s = emdash.transport.UploadTransport(newrecord=newrecord, filename=outfile, param="file_binary_image")
	# 
	# 		sidecar = s.sidecar_read()
	# 		if sidecar:
	# 			print "This scan already appears to be uploaded! Check record ID %s"%sidecar.get('name')
	# 			return []
	# 
	# 		return [m, s]
	# 
	# 
	# 	elif len(idmap[match]) == 1:
	# 		matches = matches.pop()
	# 		print "Found match for %s: %s"%(match, matches)
	# 		newrecord = {}
	# 		newrecord["name"] = -1
	# 		newrecord["rectype"] = 'scan'
	# 		newrecord["parents"] = [matches]
	# 		newrecord.update(self.applyparams)
	# 
	# 		return [emdash.transport.UploadTransport(newrecord=newrecord, filename=outfile, param="file_binary_image")]
	# 
	# 
	# 	elif len(idmap[match]) > 1:
	# 		print "Ambiguous matches for %s: %s -- skipping"%(match, matches)
	# 		return []

