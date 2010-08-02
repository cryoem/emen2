import datetime
import collections
# Host Name N/A HTTP AUTH        Time Finished      ["Method Name]  Path      [Protocol"] Response  Size
#                 USERID                                                                    Code   (bytes)
# 127.0.0.1  -      -     [Thu May 21 12:43:46 2009] "GET           /db/rec/  HTTP/-.-"     200     9714
# 127.0.0.1 - - [Thu May 21 12:48:18 2009] /db/rec/ 200 9714
# LOG_WEB:publicresource.py :: 127.0.0.1 - - [Thu May 21 12:43:41 2009] /db/__reload_views/ 200 3159
HOST_NAME = 0
SKIP = 1
SKIP = 2
TIME = 3,7
METHOD = 8
PATH = 9
PROTOCOL = 10
RESPONSE_CODE = 11
SIZE = 12
CTIME = "[%a %b %d %H:%M:%S %Y]"
class LogLine(dict):
	def __init__(self, host, rtime, request, response_code, size, extra, time_fmt=CTIME):
		self.__locked = False
		self.__tfmt = time_fmt
		self['host'], self['request'], self['response_code'], self['size'] = host, request, response_code, size
		if not hasattr(rtime, 'strptime'): rtime = datetime.datetime.strptime(rtime, CTIME)
		self['rtime'] = rtime
		self['extra'] = extra
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
		print line
		host = line[0]
		rtime = line[3]
		request = line[4]
		response_code = int(line[5])
		size = int(line[6])
		extra = None#line[7:]
		rtime = datetime.datetime.strptime(rtime,time_fmt)
		self = cls(host, rtime, request, response_code, size, extra, time_fmt)
		self.__line = tline
		self.line = line
		return self

	def __repr__(self): return "LogLine(%r)" % ' '.join(self.__line.split())
	def __str__(self):
		d = dict(self)
		d['rtime'] = d['rtime'].strftime(self.__tfmt)
		return '%(host)s - - %(rtime)s %(request)s %(response_code)s %(size)s\n' % d

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
			if not isinstance(line, LogLine):
				line = LogLine.from_line(line)
			for k,v in line.items():
				self.data[k][v].append(line)

	@classmethod
	def from_file(cls, file):
		lines= []
		for line in file:
			try:
				lines.append(LogLine.from_line(line))
			except: pass
		return cls(*lines)


if __name__ == '__main__':
	rcodes = collections.defaultdict(int)
