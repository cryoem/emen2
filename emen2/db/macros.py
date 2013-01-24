# $Id$
"""EMEN2 Macros

Classes:
    Macro: Base Macro
    macro_*: A number of macros included by default

"""

import random
import operator
import cgi
import re

import emen2.util.listops
import emen2.db.exceptions

# Convenience
ci = emen2.util.listops.check_iterable
ValidationError = emen2.db.exceptions.ValidationError

# From http://stackoverflow.com/questions/2212933/python-regex-for-reading-csv-like-rows
parser = r"""
    \s*                 # Any whitespace.
    (                   # Start capturing here.
      [^,"']+?          # Either a series of non-comma non-quote characters.
      |                 # OR
      "(?:              # A double-quote followed by a string of characters...
          [^"\\]|\\.    # That are either non-quotes or escaped...
       )*               # ...repeated any number of times.
      "                 # Followed by a closing double-quote.
      |                 # OR
      '(?:[^'\\]|\\.)*' # Same as above, for single quotes.
    )                   # Done capturing.
    \s*                 # Allow arbitrary space before the comma.
    (?:,|$)             # Followed by a comma or the end of a string.
    """


def parse_args(args):
    r = re.compile(parser, re.VERBOSE)
    ret = []
    for i in r.findall(args):
        if not i:
            continue
        if i[0] in ['"',"'"] and i[0]==i[-1]:
            i = unicode(i[1:-1])
        else:
            try:
                i = float(i)
            except ValueError:
                i = unicode(i)
        ret.append(i)
    return ret



##### Macro #####

class Macro(object):

    keyformat = 's'

    def __init__(self, cache=None, db=None):
        self.cache = cache
        self.db = db

    ##### Extensions #####

    registered = {}
    @classmethod
    def register(cls, name):
        def f(o):
            if name in cls.registered:
                raise ValueError("""%s is already registered""" % name)
            cls.registered[name] = o
            return o
        return f

    ##### Macro processing #####
        
    # Pre-cache if we're going to be doing alot of records.. This can be a substantial improvement.
    def preprocess(self, params, recs):
        pass

    # Run the macro
    def process(self, params, rec):
        return "Macro"

    # Render the macro
    def render(self, params, rec, value=None):
        value = value or self.process(params, rec)
        if hasattr(value, '__iter__'):
            value = ", ".join(map(unicode, value))
        return unicode(value)

    # Get some info about the macro
    def macro_name(self, params):
        return unicode("Macro")




@Macro.register('name')
class macro_name(Macro):
    """name macro"""
    keyformat = 'd'

    def process(self, params, rec):
        return rec.name


    def macro_name(self, params):
        return "Record Name"



@Macro.register('parents')
class macro_parents(Macro):

    def process(self, params, rec):
        rectype, _, recurse = params.partition(",")
        recurse = int(recurse or 1)
        return self.db.rel.parents(rec.name, rectype=rectype, recurse=recurse)


    def macro_name(self, params):
        return "Parents: %s"%params



@Macro.register('recname')
class macro_recname(Macro):
    """recname macro"""

    def process(self, params, rec):
        return self.db.record.render(rec) #cache=self.cache


    def macro_name(self, params):
        return "Record ID"


@Macro.register('childcount')
class macro_childcount(Macro):
    """childcount macro"""
    keyformat = 'd'

    def preprocess(self, params, recs):
        rectypes = params.split(",")
        # ian: todo: recurse = -1..
        children = self.db.rel.children([rec.name for rec in recs], rectype=rectypes, recurse=3)
        for rec in recs:
            key = self.cache.get_cache_key('rel.children', rec.name, *rectypes)
            self.cache.store(key, len(children.get(rec.name,[])))


    def process(self, params, rec):
        """Now even more optimized!"""
        rectypes = params.split(",")
        key = self.cache.get_cache_key('rel.children', rec.name, *rectypes)
        hit, children = self.cache.check_cache(key)
        if not hit:
            children = len(self.db.rel.children(rec.name, rectype=rectypes, recurse=3))
            self.cache.store(key, children)

        return children


    def macro_name(self, params):
        return "Childcount: %s"%(params)



@Macro.register('img')
class macro_img(Macro):
    """image macro"""

    def process(self, params, rec):
        default = ["file_binary_image","640","640"]
        ps = params.split(",")
        for i,v in list(enumerate(ps))[:3]:
            default[i] = v

        param, width, height = default

        pd = self.db.paramdef.get(param)

        if pd.vartype=="binary":
            if pd.iter:
                bdos = rec[param]
            else:
                bdos = [rec[param]]

        else:
            return "(Invalid parameter)"

        #print bdos
        if bdos == None:
            return "(No Image)"

        ret = []
        for i in bdos:
            try:
                bdoo = self.db.binary.get(i, filt=False)
                fname = bdoo.get("filename")
                bname = bdoo.get("filepath")
                root = "TEST" # emen2.db.config.get('web.root')
                ret.append('<img src="%s/download/%s/%s" style="max-height:%spx;max-width:%spx;" alt="" />'%(root,i[4:], fname, height, width))
            except (KeyError, AttributeError, emen2.db.exceptions.SecurityError):
                ret.append("(Error: %s)"%i)

        return "".join(ret)

    def macro_name(self, params):
        return "Image Macro"



@Macro.register('childvalue')
class macro_childvalue(Macro):
    """childvalue macro"""

    def process(self, params, rec):
        name = rec.name
        children = self.db.record.get(self.db.rel.children(name))
        return [i.get(params) for i in children]


    def macro_name(self, params):
        return "Child Value: %s"%params



@Macro.register('parentvalue')
class macro_parentvalue(Macro):
    """parentvalue macro"""

    def process(self, params, rec):
        p = params.split(",")
        param, recurse, rectype = p[0], 1, None

        if len(p) == 3:
            param, recurse, rectype = p
        elif len(p) == 2:
            param, recurse = p

        recurse = int(recurse or 1)
        name = rec.name
        parents = self.db.record.get(self.db.rel.parents(name, recurse=recurse, rectype=rectype))
        return filter(None, [i.get(param) for i in parents])


    def macro_name(self, params):
        return "Parent Value: %s"%params



@Macro.register('or')
class macro_or(Macro):
    """parentvalue macro"""

    def process(self, params, rec):
        ret = None
        for param in params.split(","):
            ret = rec.get(params.strip())
            if ret != None:
                return ret

    def macro_name(self, params):
        return " or ".join(params.split(","))



@Macro.register('thumbnail')
class macro_thumbnail(Macro):
    """tile thumb macro"""

    def process(self, params, rec):
        root = "TEST" # emen2.db.config.get('web.root')
        format = "jpg"
        defaults = ["file_binary_image", "thumb", "jpg"]
        params = (params or '').split(",")

        for i,v in enumerate(params):
            if v:
                defaults[i]=v

        bdos = rec.get(defaults[0])
        if not hasattr(bdos,"__iter__"):
            bdos = [bdos]


        return "".join(['<img class="e2l-thumbnail" src="%s/download/%s/%s.%s.%s?size=%s&amp;format=%s" alt="" />'%(
                root, bid, bid, defaults[1], defaults[2], defaults[1], defaults[2]) for bid in filter(lambda x:isinstance(x,basestring), bdos
                )])


    def macro_name(self, params):
        return "Thumbnail Image"




##### Editing macros #####

@Macro.register('checkbox')
class macro_checkbox(Macro):
    """draw a checkbox for editing values"""

    def process(self, params, rec):
        args = parse_args(params)
        return self._process(rec, *args)

    def _process(self, rec, param, value, label=None, *args, **kwargs):
        checked = ''
        if value in ci(rec.get(param)):
            checked = 'checked="checked"'

        # grumble..
        labelid = 'e2-edit-checkbox-%032x'%random.getrandbits(128)

        # Need to put in a hidden input element so that empty sets will still be submitted.
        return """
            <input id="%s" type="checkbox" name="%s" data-param="%s" value="%s" %s />
            <label for="%s">%s</label>
            <input type="hidden" name="%s" value="" />"""%(labelid, param, param, value, checked, labelid, label or value, param)

    def macro_name(self, params):
        return "Checkbox:", params




__version__ = "$Revision$".split(":")[1][:-1].strip()
