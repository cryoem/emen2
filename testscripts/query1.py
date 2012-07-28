# $Id$
import emen2.test

class Block(object):
    def __init__(self, block, tail=None):
        self._block = block.split()
        self._tail = tail

    @staticmethod
    def split(string, delimiter='.'):
        return string.split(delimiter, 1)

    @classmethod
    def make_block(cls, string, delimiter='.'):
        return cls(*cls.split(string, delimiter))

    def get_next_block(self, delimiter='.'):
        cls = self.__class__
        if self._tail:
            print self._tail
            return cls.make_block(self._tail, delimiter)

    def get_block(self): return self._block

class Processor(object):
    _verbs = {}
    verbs = property(lambda self: set(self._verbs))
    _default_command = '_default'

    def __init__(self):
        self._line = []
        self._words = set()

    @classmethod
    def add_command(cls, name, processor, default=False):
        cls._verbs[name] = processor
        if default:
            cls._verbs[cls._default_command] = processor


    def process_input(self, txt, data):
        block = Block.make_block(txt)
        while block is not None:
            print block, ' '.join(block.get_block())
            data, block = self.process_block(block, data)
        return data

    def process_block(self, block, data):
        self._line = block.get_block()
        self._words = set(self._line)
        commands = (self.verbs & self._words) or [self._default_command]
        command = commands.pop()
        if (command != self._default_command and self._line.count(command) != 1) or len(commands) != 0:
            raise ValueError, 'only one command per block'
        processor = self._verbs[command]
        return processor.execute((x for x in self._line if x != command), data), block.get_next_block()

def iconc(iterlist):
    for iter in iterlist:
        for item in iter:
            yield item

class Find(object):
    RECORDDEF, PARAMDEF = 1, 2

    def __init__(self): self._state = 0

    def _checkname1(self, name):
        exclude = False
        if name.startswith('!'):
            exclude, name = True, name[1:]
        return exclude, name

    def execute(self, line, data):
        paramdefs, recorddefs = self.process_line(line)
        print recorddefs
        output = set(iconc(emen2.test.db.getindexbyrectype(name) for exclude,name in recorddefs if not exclude))
        print output
        output -= set(iconc(emen2.test.db.getindexbyrectype(name) for exclude,name in recorddefs if exclude))
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
        self._state = 0
        return output & data

    def set_state(self, word, error=False):
        result = False
        if word.lower() in set(['recorddef','rectype','protocol']):
            self._state  = self.RECORDDEF
        elif word.lower() in set(['paramdef', 'param']):
            self._state = self.PARAMDEF
        elif self._state == 0:
            raise ValueError, 'Unrecognized symbol: %s' % word
        else:
            result = True
        return result

    def process_line(self, line):
        paramdefs, recorddefs = set(), set()

        for word in line:
            if self.set_state(word):
                if self._state == self.RECORDDEF:
                    recorddefs.add(self._checkname1(word))
                elif self._state == self.PARAMDEF:
                    item = list(word.partition('=')[::2])
                    item[0:1] = self._checkname1(item[0])
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
