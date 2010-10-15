# $Id$
import emen2.test

class Block(object):
	def __init__(self, block, tail=None):
		self.__block = block.split()
		self.__tail = tail

	@staticmethod
	def split(string, delimiter='.'):
		return string.split(delimiter, 1)

	@classmethod
	def make_block(cls, string, delimiter='.'):
		return cls(*cls.split(string, delimiter))

	def get_next_block(self, delimiter='.'):
		cls = self.__class__
		if self.__tail:
			print self.__tail
			return cls.make_block(self.__tail, delimiter)

	def get_block(self): return self.__block

class Processor(object):
	__verbs = {}
	verbs = property(lambda self: set(self.__verbs))
	__default_command = '__default'

	def __init__(self):
		self.__line = []
		self.__words = set()

	@classmethod
	def add_command(cls, name, processor, default=False):
		cls.__verbs[name] = processor
		if default:
			cls.__verbs[cls.__default_command] = processor


	def process_input(self, txt, data):
		block = Block.make_block(txt)
		while block is not None:
			print block, ' '.join(block.get_block())
			data, block = self.process_block(block, data)
		return data

	def process_block(self, block, data):
		self.__line = block.get_block()
		self.__words = set(self.__line)
		commands = (self.verbs & self.__words) or [self.__default_command]
		command = commands.pop()
		if (command != self.__default_command and self.__line.count(command) != 1) or len(commands) != 0:
			raise ValueError, 'only one command per block'
		processor = self.__verbs[command]
		return processor.execute((x for x in self.__line if x != command), data), block.get_next_block()

def iconc(iterlist):
	for iter in iterlist:
		for item in iter:
			yield item

class Find(object):
	RECORDDEF, PARAMDEF = 1, 2

	def __init__(self): self.__state = 0

	def __checkname1(self, name):
		exclude = False
		if name.startswith('!'):
			exclude, name = True, name[1:]
		return exclude, name

	def execute(self, line, data):
		paramdefs, recorddefs = self.process_line(line)
		print recorddefs
		output = set(iconc(emen2.test.db.getindexbyrecorddef(name) for exclude,name in recorddefs if not exclude))
		print output
		output -= set(iconc(emen2.test.db.getindexbyrecorddef(name) for exclude,name in recorddefs if exclude))
		print output

		tmpset = set()
		removeset = set()
		for exclude, name, value in paramdefs:
			if value is not '': recset = emen2.test.db.getindexbyvalue(name, value)
			else: recset = emen2.test.db.getindexbyvalue(name, None)

			if not exclude: tmpset |= recset
			else: removeset |= recset

		print tmpset
		if tmpset != set():
			if output == set():
				output = tmpset
			else:
				output &= tmpset
		output -= removeset
		self.__state = 0
		return output & data

	def set_state(self, word, error=False):
		result = False
		if word.lower() in set(['recorddef','rectype','protocol']):
			self.__state  = self.RECORDDEF
		elif word.lower() in set(['paramdef', 'param']):
			self.__state = self.PARAMDEF
		elif self.__state == 0:
			raise ValueError, 'Unrecognized symbol: %s' % word
		else:
			result = True
		return result

	def process_line(self, line):
		paramdefs, recorddefs = set(), set()

		for word in line:
			if self.set_state(word):
				if self.__state == self.RECORDDEF:
					recorddefs.add(self.__checkname1(word))
				elif self.__state == self.PARAMDEF:
					item = list(word.partition('=')[::2])
					item[0:1] = self.__checkname1(item[0])
					paramdefs.add(tuple(item))
		return paramdefs, recorddefs


txt = raw_input('> ')
a = Processor()
Processor.add_command('find', Find(), default=True)
while txt:
	try:
		data = a.process_input(txt, emen2.test.db.getindexbycontext())
		print data
	except ValueError, e:
		print 'E', e
	txt = raw_input('> ')
__version__ = "$Revision$".split(":")[1][:-1].strip()
