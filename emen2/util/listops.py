# $Id: listops.py,v 1.42 2012/07/28 06:31:18 irees Exp $
import collections
import itertools
from UserDict import DictMixin
from functools import partial
import emen2.db.datatypes



def filter_dict_zero(d):
    """@return Filter dict for items with values > 0"""
    return dict(filter(lambda x:len(x[1])>0, d.items()))



def filter_dict_none(d):
    """@return Filter dict for items with values != None"""
    return dict(filter(lambda x:x[1]!=None, d.items()))




# Return the first item from a list, or None.
def first_or_none(items):
    items = items or []
    result = None
    if len(items) > 0:
        if hasattr(items, 'keys'):
            result = items.get(first_or_none(items.keys()))
        else:
            result = iter(items).next()
    return result


filter_none = lambda x:x or x==0


def invert(d):
    """Invert a dictionary"""
    ret = {}
    for k,v in d.items():
        for v2 in v:
            ret[v2]=k
    return ret




def check_iterable(value):
    if not hasattr(value,"__iter__"):
        value = [value]
    return filter(filter_none, value)




def get(collection, key, default=None):
    '''allows getting an item from a collection like dict.get does'''
    try: return collection[key]
    except KeyError: return default
    except IndexError: return default



def remove(collection, keys):
    '''remove a set of elements from a dictionary'''
    if not hasattr(keys, '__iter__'):
        keys = set([keys])
    else:
        keys = set(keys)
    for key in keys:
        try: del collection[key]
        except KeyError: pass



def adjust(iter_, *items_):
    meth = None
    if hasattr(iter_, 'update'): meth = iter_.update
    elif hasattr(iter_, 'extend'): meth = iter_.extend
    if meth is not None:
        for l in items_: meth(l)
    else:
        iter_ = type(iter_)(itertools.chain(iter_, *items_))
    return iter_



def combine_lists(sep=' ', *args):
    return (sep.join(x) for x in zip(*args))







def filter_dict(dict, allowed, pred=lambda key, list_: key in list_):
    '''remove items from a dictionary according to a list and a test function

    >>> filter_dict(dict(a=1, b=2, c=3, d=4), ['a', 'b', 'c'])
    {'a': 1, 'b': 2, 'c':3}
    >>> filter_dict(dict(a=1, b=2, c=3, d=4), ['a', 'b', 'c'], lambda key, lis: key not in lis)
    {'d': 4}
    '''
    result = {}
    [ result.update([(key, dict[key])]) for key in dict if pred(key, set(allowed)) ]
    return result


#pick items from a dict
pick = filter_dict
#drop items from a dict
drop = partial(filter_dict, pred=(lambda x,y: x not in y))



def chunk(l, count=1000):
    '''chunk a list into segments of length count'''
    ll = list(l)
    return (ll[i:i+count] for i in xrange(0, len(ll), count))



def groupchunk(list_, grouper=lambda x: x[0]==x[1], itemgetter=lambda x:x):
    '''groups items in list as long as the grouper function returns True

    >>> chunk([1,3,2,4,3,2,4,5,3,1,43,2,1,1])
    [[1], [3], [2], [4], [3], [2], [4], [5], [3], [1], [43], [2], [1, 1]]
    >>> chunk([1,3,2,4,3,2,4,5,3,1,43,2,1,1], lambda x: x[0]<x[1])
    [[1, 3], [2, 4], [3], [2, 4, 5], [3], [1, 43], [2], [1], [1]]
    '''
    if hasattr(list_, '__iter__') and not isinstance(list_, list):
        list_ = list(list_)
    result = [[list_[0]]]
    for x in xrange(len(list_)-1):
        window = list_[x:x+2]
        if not grouper(window):
            result.append([])
        result[-1].append(itemgetter(window[1]))
    return result



def typepartition(names, *types):
    ret = collections.defaultdict(list)
    other = list()
    for name in names:
        found = False
        for t in types:
            if isinstance(name, t):
                found = True
                ret[t].append(name)
        if not found:
            other.append(name)

    return [ret.get(t, []) for t in types]+[other]


def filter_partition(func, iter_):
    t = []
    f = []
    for i in iter_:
        if func(i) == True:
            t.append(i)
        else:
            f.append(i)
    return t, f



def partition(iter_, char):
    '''partition iterable on given element

    >>> partition([1,2,3,2,3,4,5,6,':',2], ':')
    [[1, 2, 3, 2, 3, 4, 5, 6], [':'], [2]]
    >>> partition([1,2,3,2,3,4,5,6,':'], ':')
    [[1, 2, 3, 2, 3, 4, 5, 6], [':'], []]
    >>> partition([1,2,3,2,3,4,5,6], ':')
    [[1, 2, 3, 2, 3, 4, 5, 6], [], []]'''
    res = chunk(iter_, lambda x: x[0] != char)
    if res:
        if res[0] and res[0][-1] == char:
            del res[0][-1]
            res.insert(1, [char])
        if len(res) > 2: res = [res[0], res[1], combine(*res[2:])]
    while len(res) < 3: res.append([])
    return res



def partition_dbobjects(iter_):
    ret1 = []
    ret2 = []
    for i in iter_:
        if isinstance(i, emen2.db.dataobject.BaseDBObject):
            ret2.append(i)
        else:
            ret1.append(i)
    return ret1, ret2



def combine(*lists, **kw):
    '''combine iterables return type is the type of the first one

    >>> combine([1,2,3,4], [2,3,4,5])
    [1, 2, 3, 4, 2, 3, 4, 5]
    >>> combine([1,2,3,4], [2,3,4,5], dtype=tuple)
    (1, 2, 3, 4, 2, 3, 4, 5)
    >>> combine([1,2,3,4], [2,3,4,5], dtype=set)
    set([1, 2, 3, 4, 5])
    >>> combine(set([1,2,3,4]), [2,3,4,5])
    set([1, 2, 3, 4, 5])
    '''
    dtype = kw.get('dtype', None) or type(lists[0])
    if hasattr(lists[0], 'items'):
        lists = [list_.items() for list_ in lists]
    return dtype(itertools.chain(*lists))


def flatten(a):
    '''flatten a dict with lists as items into a set

    >>> a={1:[2,3],4:[5,6]}
    >>> flatten(a)
    set([1, 2, 3, 4, 5, 6])
    '''
    return combine(*([a.keys()]+a.values()), dtype=set)




# From database
def tolist(d, dtype=None):
    return oltolist(d, dtype=dtype)[1]




def oltolist(d, dtype=None):
    dtype = dtype or list
    ol = False
    result = None

    if isinstance(d, dtype): pass

    elif isinstance(d, (dict, DictMixin)) or not hasattr(d, "__iter__"):
        d = [d]
        ol = True

    if not isinstance(d, dtype):
        d = dtype(d)

    return ol, d


def dictbykey_0(l, key):
    result = {}
    for i in l:
        result.setdefault(i.get(key), {}).update(i)
    return result

def dictbykey_1(l, key):
    result = collections.defaultdict(list)
    for i in l:
        result[i.get(key)].append(i)
    return result

def dictbykey_2(l, key):
    l = sorted(l, key=lambda x: x.get(key))
    l = groupchunk(l, grouper=lambda (a,b): a.get(key)==b.get(key))
    l = dict( (x[0].get(key), x) for x in l)
    return l

def dictbykey(l, key='name'):
    return dict( (i.get(key), i) for i in l )




def groupbykey(l, key, dtype=None):
    dtype = dtype or list
    d = collections.defaultdict(dtype)
    for i in l:
        k = i.get(key)
        d[k] = adjust(d[k], i)
    return dict(d)




def typefilter(l, types=None):
    if not types:
        types=str
    return [x for x in l if isinstance(x,types)]
    #return filter(lambda x:isinstance(x, types), l)




def test_get():
    print '1 == ',  get( {2:2, 3:3, 1:1}, 1 )
    print '1 == ', get( {2:2, 3:3}, 1, 1 )
    print 'None == ', get( {2:2, 3:3}, 1)

def run_tests():
    test_get()

if __name__ == '__main__':
    run_tests()
__version__ = "$Revision: 1.42 $".split(":")[1][:-1].strip()
