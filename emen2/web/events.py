import functools
import threading
from emen2.util import registry

#NOTE: this is probably unnecessary... All it adds is error-handling if the callback is not 
     # actually callable
class Callback(object):
    '''wrap a callback to be associated with an event'''
    def __init__(self, cb, *args, **kwargs):
        if args or kwargs:
            cb = functools.partial(cb, *args, **kwargs)
        self.cb = cb

    def __call__(self, *args, **kwargs):
        result = self.cb
        if callable(self.cb):
            result = self.cb(*args, **kwargs)
        return result

class Event(object):
    '''Holds the callbacks to respond to and the observers to notify on an event'''

    _cb_lock = threading.RLock()
    _o_lock = threading.RLock()
    def __init__(self, name):
        self.name = name
        self.callbacks = []
        self.observers = []

    def add_observer(self, cb, *args, **kwargs):
        '''Add an observer, it will be called with arguments from *args and **kwargs
        as well as the result returned by each callback for this event'''
        with self._o_lock:
            self.observers.append(functools.partial(cb, *args, **kwargs))
        return self

    def add_cb(self, cb, *args, **kwargs):
        '''Add a callback, it will be called with the arguments from *args and **kwargs
        as well as any additional arguments passed to the __call__ method of this object'''
        with self._cb_lock:
            cb = Callback(cb, *args, **kwargs)
            self.callbacks.append(cb)
            return cb

    def add_cbs(self, cbs):
        '''Add many callbacks, argument format: { callback: (args, kwargs) }'''
        for (cb, (a, kw)) in cbs.iteritems():
            self.add_cb(cb, *a, **kw)
        return self

    def remove_cb(self, cb):
        '''Remove a callback, argument: the callback to be removed'''
        self.callbacks = [x for x in self.callbacks if x is not cb]
        return self

    def __call__(self, *args, **kwargs):
        '''Call each callback and notify every observer about its results'''
        results = []

        for cb in self.callbacks:
            result = cb(*args, **kwargs)
            with self._o_lock:
                for observer in self.observers:
                    observer(result)
            results.append(result)
        return results

@registry.Registry.setup
class EventRegistry(registry.Registry):
    '''Register an event, see emen2.util.registry for documentation'''
    child_class = Event

    events = {}
    nullevent = Event('') #Ed: I'm not sure if this is necessary

    def observe_event(self, name, cb, *args, **kwargs):
        '''Add an observer to an event'''
        with self._lock:
            self.events[name].add_observer(cb, *args, **kwargs)
            return self
