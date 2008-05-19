import time, sys
from g import LOG_INIT, LOG_INFO
import g
print dir()
import code

__all__ = ['DebugState', 'DEBUG', 'log']


DEBUG = 0
log = file ('/Users/edwardlangley/emen2/log.log', 'a')


class DebugState(object):
    '''Handles logging etc..'''
    _clstate = {}

    def __enter__(self, *args):
        print args
        self.push_state(-1)

    def __exit__(self, *args):
        self.pop_state()

    def __init__(self, value=None, buf=None, oldstdout=None, get_state=True):
        value = value or 0
        self.__dict__ = self._clstate
        if (not get_state) or (not self._clstate):
            self.__state = value
            self.__buffer = buf
            if oldstdout:
                self.oldstdout = oldstdout
                sys.stdout = self
            else:
                self.oldstdout = sys.stdout
        self.__state_stack = [value]
        self.msg(g.LOG_INIT, 'debug init state: %s' % value)

    def write(self, value):
        value = value.strip()
        if value is not str():
            self.msg(LOG_INFO, value)

    def flush(self, *args):
        self.__buffer.flush()
        self.oldstdout.flush()
    def get_state(self):
        return self.__state

    def set_state(self, state):
        self.msg(-2, 'entering: %s--leaving : %s' % (state, self.state))
        self.__state = state
    state = property(get_state, set_state)\
    
    def push_state(self, state):
        self.__state_stack.append(state)
        self.state = state

    def pop_state(self):
        if len(self.__state_stack) > 1:
            self.__state_stack.pop()
            self.state = self.__state_stack[-1]
    def get_buffer(self):
        return self.__buffer
    buffer = property(get_buffer)
    def msg(self, state, *args):
        '''general purpose logging function
        logs to disk all messages whose state is
        greater than -1'''
        if self.__buffer:
            print >>self.__buffer, time.ctime(), '<%03d>:' % state, self.print_list(args), ''
            self.__buffer.flush()
        if state >= self.__state:
            print >>self.oldstdout, '<%02d>' % state, self.print_list(args)

    def note_var(self, var):
        '''log the value of a variable and return the variable'''
        self.msg(0, 'NOTED VAR:::', var)
        return var

    def __call__(self, *args, **k):
        '''log with a state of -1'''
        join = k.get('join', ' ')
        self.msg(-1, join.join([str(x) for x in args]))

    def print_list(self, lis):
        result = []
        for i in lis: result.append(str(i))
        return str.join(' ', result)

    def debug_func(self, func):
        def result(*args, **kwargs):
            self.push_state(-1)
            self('debugging callable: %s, args: %s, kwargs: %s'  % (func, args, kwargs))
            result = func(*args, **kwargs)
            self('the callable %s returned: %s' % (repr(func), repr(result)))
            self.pop_state()
            self.last_debugged = (func, args, kwargs)
            return result
        result.__doc__ = func.__doc__
        result.__name__ = func.__name__
        return result
    
    def interact(self, locals, globals):
        interp = code.InteractiveConsole(locals)
        interp.interact('Debugging')
        