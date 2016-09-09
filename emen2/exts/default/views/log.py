# $Id: log.py,v 1.8 2012/10/18 09:41:40 irees Exp $
# Standard View imports
import functools
import collections
import os.path

import emen2.db.config
from emen2.web.view import View, AdminView
from emen2.util.loganalyzer import AccessLogFile, AccessLogLine
import datetime


class _Null: pass
def cast_arguments(*postypes, **kwtypes):
    def _func(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            out = []
            for typ, arg in itertools.izip_longest(postypes, args, fillvalue=_Null):
                if arg != _Null:
                    if typ != _Null and typ != None:
                        arg = typ(arg)
                    out.append(arg)
            for k,v in kwargs.iteritems():
                typ = kwtypes.get(k, _Null)
                if typ != _Null and typ != None:
                    kwargs[k] = typ(kwargs[k])
            return func(*args, **kwargs)
        return _inner
    return _func



class RecordNotFound(emen2.web.responsecodes.NotFoundError):
    title = 'Record Not Found'
    msg = 'Record %d not found'
    def __init__(self, msg):
        emen2.web.responsecodes.NotFoundError.__init__(self, msg)

class Reverser(object):
    def __init__(self, fil):
        self._file = fil
        self._file.seek(-1, 2)
        self.stopped = False
    def _bseek(self):
        result = False
        if self._file.tell() == 1: result = True
        else:
            self._file.seek(-2,1)
        self.stopped = result
        return result
    def next(self):
            if self.stopped: raise StopIteration
            line = []
            line.insert(0, self._file.read(1))
            if line[0] == '\n':
                line.pop()
            self._bseek()
            if not self.stopped:
                cur = self._file.read(1)
                while cur != '\n' and not self.stopped:
                    line.insert(0, cur)
                    self._bseek()
                    cur = self._file.read(1)
                self._bseek()
            return ''.join(line)
    def __iter__(self):
        try:
            while True:
                yield self.next()
        except EOFError: raise StopIteration

# class TableJS(emen2.web.templating.BaseJS):
#     def main(self):
#         super(TableJS, self).init()
#         self.files = '%s/static/js/jquery/jquery.dataTables.js' % g.ROOT
#         self.files = '%s/static/js/jquery/jquery.accordion.js' % g.ROOT

ident = lambda x:x
class Normalizer(object):
    def __init__(self, norm=ident, unnorm=ident):
        self.norm = norm
        self.unnorm = unnorm

def decorator(func):
    @functools.wraps(func)
    def _inner(func1):
        @functools.wraps(func1)
        def _inner1(*a, **kw):
            return func(func1(*a, **kw))
        return _inner1
    return _inner

@decorator
def stringify(dict_):
    sdict = {'TB': (0, '{TB} TB'), 'GB': (1, '{GB} GB'), 'MB': (2, '{MB} MB'), 'KB': (3,'{KB} KB'), 'B':(4,'{B} B')}
    fmtl =  [ x[1] for x in sorted( sdict[k] for k in (set(dict_) & set(sdict)) ) ]
    return ', '.join(fmtl).format(**dict_)


@stringify
def makereadable(val):
    vals = dict(B = val, KB = 0, MB = 0, GB = 0, TB = 0)
    def adjust(dict_, a,b):
        if dict_[a] >= 1024:
            dict_[b] = dict_[a] / 1024
            dict_[a] %= 1024
    adjust(vals, 'B', 'KB')
    adjust(vals, 'KB', 'MB')
    adjust(vals, 'MB', 'GB')
    adjust(vals, 'GB', 'TB')
    vals = dict( (k,v) for k,v in vals.iteritems() if v != 0 ) or {'B':0}
    return vals

@View.register
@AdminView.attach
class LogAnalysis(View):#AdminView):
    template = '/pages/log'
    
    @View.add_matcher("^/log/main/(?P<dataset>.*)/$")
    def main(self, dataset='host', start=0, end=100, sort='host', reverse=1):
        pass

    def _getlines(self, file_, logclass, start, end, reverse=True, index=None):
        lines, errors = [],[]

        logpath = emen2.db.config.get('paths.log')
        with file(os.path.join(logpath, file_)) as f:
            extra = lambda x:x
            if reverse: extra = Reverser

            for n, line in enumerate( x for x in extra(f) if x.strip() ): #filter out blank lines and return n,line = ( line #, line )
                try:
                    if n >= end: break
                    elif start <= n:
                        lines.append(line)
                except Exception, e:
                    emen2.db.log.error(e)
                    errors.append('problem, line: %r' % line)

        logfile = logclass(*lines, index=index)
        return logfile, errors

    @View.add_matcher("^/log/access/(?P<dataset>.*)/$")
    @cast_arguments(start=int, end=int, reverse=lambda x: bool(int(x)), dataset=lambda x: x.split('/'))
    def access(self, dataset='host', start=0, end=100, sort='host', reverse=True):
        name = dataset[0]
        index = set([name])
        linefilter = collections.defaultdict(set)

        jsfilter = []
        data_cast = dict(AccessLogLine.order)
        for x in dataset[1:]:
            n = x.split(':', 1)
            print n
            if (len(n) == 2) and (n[0] in AccessLogLine.labels):
                label, val = n
                index.add(label)
                linefilter[label].add(data_cast.get(label, ident)(val))
            else:
                jsfilter.append(x)

        ctx = self.db._getctx()
        if not ctx.checkadmin():
            linefilter['username'] = set([ctx.username])

        logfile, errors = self._getlines('access.log', AccessLogFile, start, end, reverse=reverse, index=index)

        data = ldata = logfile.data.get(name, {})
        if linefilter:
            print 1
            data = {}
            for name, lines in ldata.iteritems():
                data[name] = []
                for line in lines:
                    to_check = set(line) & set(linefilter)
                    add = True

                    for key in to_check:
                        val = line[key]
                        if val not in linefilter[key]:
                            add = False

                    if add:
                        data[name].append(line)
                if len(data[name]) == 0: del data[name]



        print linefilter, jsfilter
        self.ctxt.update(
            sort=sort, errors=errors, name=name,

            title='Access Log',
            dataset=data,
            filter_str=' '.join(jsfilter),

            viewargs=dict(
                start=start, end=end, sort=sort, reverse=int(reverse)
            ),

            norm = dict(
                    rtime = Normalizer(
                        lambda x: (x and x.strftime('%Y%m%d%H')),
                        lambda x: (x and datetime.datetime.strptime(x, '%Y%m%d%H'))
                    ),
                    size = Normalizer(
                        lambda x: x/(1024),
                        lambda x: ('%s-%s' % (makereadable(x*(1024)), makereadable(x*1024 + 1023)))
                    )
                ).get(name, Normalizer())
        )
__version__ = "$Revision: 1.8 $".split(":")[1][:-1].strip()
