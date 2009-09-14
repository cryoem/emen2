from __future__ import with_statement
import sys, time
import contextlib
import threading

class Ticker(object):
    def __init__(self):
        self.days = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
    def tick(self):
        self.seconds += 1
        if self.seconds >= 60:
            self.minutes += self.seconds/60
            self.seconds = self.seconds % 60
        if self.minutes >= 60:
            self.hours += self.minutes/60
            self.minutes = self.minutes % 60
        if self.hours >= 24:
            self.days += self.hours/60
            self.hours = self.hours % 60
    def print_(self):
        return '%d days %02d:%02d:%02d' % (self.days, self.hours, self.minutes, self.seconds)


class AsciiSpinner(threading.Thread):

    def __init__(self, delay=1):
        threading.Thread.__init__(self)
        self.delay = delay
        self.running = True

    def run(self):
       while self.running:
            print self.running
            #for char in '/-\|': # there should be a backslash in here.
				#for char in '.oOo': # there should be a backslash in here.
            #for char in ':.,;': # there should be a backslash in here.
            #for char in '_-^-': # there should be a backslash in here.
            #for char in '<^>v': # there should be a backslash in here.
            #for char in '1234567890': # there should be a backslash in here.
            a = Ticker()
            while 1:
                if not self.running:
                    break # this is needed so it doesn't perform a full rotation if it isn't running.
                a.tick()
                sys.stdout.write(a.print_())
                sys.stdout.flush()
                time.sleep(self.delay)
                sys.stdout.write('\r') # this should be backslash r.


@contextlib.contextmanager
def spinning_distraction():
    thread = AsciiSpinner()
    thread.start()
    try:
       yield
    finally:
       sys.stdout.write(' ')
       sys.stdout.flush()
       sys.stdout.write('\r')
       print 'running == False'
       thread.running = False

# ################ #
# ################ #

def main():
    with spinning_distraction():
		while 1:
			time.sleep(5) # pretend this is real work here.


if __name__ == '__main__':
    main()

