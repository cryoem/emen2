import re
import datetime
import collections
import itertools
# Host Name N/A HTTP AUTH        Time Finished      ["Method Name]  Path      [Protocol"] Response  Size
#                 USERID                                                                    Code   (bytes)
# 127.0.0.1  -      -     [Thu May 21 12:43:46 2009] "GET           /db/rec/  HTTP/-.-"     200     9714
# 127.0.0.1 - - [Thu May 21 12:48:18 2009] /db/rec/ 200 9714
# LOG_WEB:publicresource.py :: 127.0.0.1 - - [Thu May 21 12:43:41 2009] /db/__reload_views/ 200 3159

#default time format
CTIME = "[%a %b %d %H:%M:%S %Y]"

#constants for decoding a split log line
HOST = 0
CTXID = 1
USERNAME = 2
TIME = 3
REQUEST = 4
RESPONSE_CODE = 5
SIZE = 6

class LogLine(dict):
	_timepat = re.compile('([0-9][^:]*:){2}[^:]*')
	_hostpat = re.compile('\d{,3}[.]\d{,3}[.]\d{,3}[.]\d{,3}')
	def __init__(self, header, message):
		header = header.strip().lstrip('-!>')
		#message = message.strip()
		self.inp = (header, message)

		data = header.rsplit(':', 3)
		time = self._timepat.match(data.pop(0))
		if time: time = time.group()
		else: time = '-'

		if len(data) == 1: data.append('')
		if len(data) == 2: data.append('')

		level, file_, line = data[:3]
		extra = tuple(data[3:])

		self.update(
			time=time,
			level=level,
			file=file_,
			line=line
		)
		self['message'] = message

	@classmethod
	def from_line(cls, line):
		line = line.split(' ::',1)

		if line[0] == '':
			line[0] = '-:-:-:-' # make sure header parses correctly
		elif not line[0][0].isdigit():
			line.insert(0, '-:-:-:-') # make sure header parses correctly
		elif cls._hostpat.match(line[0]):
			line.insert(0, '-:-:-:-') # make sure header parses correctly

		if len(line) == 1: line.append('')
		line[1] = line[1].strip()

		if any(not x for x in line):
			print ' '.join(line)
		return cls(*line)

class LogFile1(object):
	def __init__(self, *lines):
		self.data = collections.defaultdict(lambda:collections.defaultdict(list))
		self.lines = []

		for line in lines:
			if not isinstance(line, LogLine):
				line = LogLine.from_line(line)
			self.lines.append(line)
			for k,v in line.items():
				self.data[k][v].append(line)

	@classmethod
	def from_file(cls, file):
		'''
		-> read line
		-> store line
		-> read next line
		->  if line begins with space, store it
		->  otherwise,
		->    join cache
		->    reset to current line
		'''
		lines, line_cache, line = [], [], None
		for line in file:
			line = line.rstrip()
			if not line: continue

			if line[0].isspace(): line_cache.append(line)
			else:
				lines.append('\n'.join(line_cache))
				line_cache = [line]

		if line_cache:
			lines.append('\n'.join(line_cache))

		out = []
		for line in lines:
			try:
				out.append(LogLine.from_line(line))
			except Exception, e:
				raise
				print 'error', e, 'line:', line

		return cls(*lines)



class AccessLogLine(dict):
	def timeconv(self, tm=None):
		result = tm or None
		if not hasattr(tm, 'strptime') and tm:
			result = datetime.datetime.strptime(tm, CTIME)
		return result

	def __init__(self, *args, **kwargs):
		self.__locked = False

		self.order = kwargs.pop('order', ( # get the field order and types
				('host',str), ('ctxid',str),
				('username',str), ('rtime',self.timeconv),
				('request', str), ('response_code', long),
				('size', long), ('resource', str)
		))

		values = ( # combine the order with the passed values, and cast the values
			( k, typ( v or kwargs.get(k,typ()) ) ) for k,typ,v in itertools.izip_longest(*zip(*self.order) + [args], fillvalue='') if k != ''
		)

		values = dict( (k,v) for k, v in values )

		self.__tfmt = kwargs.pop('time_fmt', CTIME)

		self.update(values)
		if len(args) > len(values):
			self['extra'] = tuple(args[len(values):])

		self.__locked = True

	@classmethod
	def from_line(cls, line, time_fmt=CTIME):
		line = line.partition(' :: ')
		line = line[-1] or line[0]
		tline = line
		line = (x.strip() for x in line.split())
		out = []
		cls.__JOIN = False
		def toggle(): cls.__JOIN = not cls.__JOIN
		sschar = set(['"', '['])
		eschar = set(['"', ']'])
		for word in line:
			if not cls.__JOIN:
				if any( word.startswith(c) for c in sschar ): toggle()
				out.append([word])
			else:
				out[-1].append(word)
				if any( word.endswith(c) for c in eschar ): toggle()
		line = [' '.join(item) for item in out]
		self = cls(*line, time_fmt=time_fmt)
		self.__line = tline
		self.line = line
		return self

	def __repr__(self): return "AccessLogLine(%s)" % dict.__repr__(self)
	def __str__(self):
		d = dict(self)
		d['rtime'] = (d['rtime'].strftime(self.__tfmt) if d['rtime'] else '-')
		out = []
		for k,_ in self.order: out.append(str(d.get(k, '-') or '-'))
		return ' '.join(out)

	def __setitem__(self, key, value):
		if self.__locked == True:
			raise NotImplementedError, 'read only'
		else:
			dict.__setitem__(self, key, value)
	def __getattr__(self, name):
		try: return dict.__getattr__(self, name)
		except:
			if name in self: return self[name]
			else: raise

class LogFile(object):
	def __init__(self, *lines):
		self.data = collections.defaultdict(lambda:collections.defaultdict(list))
		self.lines = []

		for line in lines:
			if not isinstance(line, AccessLogLine):
				line = AccessLogLine.from_line(line)
			self.lines.append(line)
			for k,v in line.items():
				self.data[k][v].append(line)

	@classmethod
	def from_file(cls, file):
		lines= []
		for line in file:
			try:
				lines.append(AccessLogLine.from_line(line))
			except: pass
		return cls(*lines)


if __name__ == '__main__':
	rcodes = collections.defaultdict(int)
