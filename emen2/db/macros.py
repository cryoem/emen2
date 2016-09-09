# $Id: macros.py,v 1.77 2013/06/20 23:05:53 irees Exp $
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

# Markdown and Markupsafe are required now.
import markdown
from markupsafe import Markup, escape

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
    keyformat = 'str'

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

    @classmethod
    def get_macro(cls, name, *args, **kwargs):
        if name not in cls.registered:
            return macro_dummy(*args, **kwargs)
        return cls.registered[name](*args, **kwargs)

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


# Dummy
@Macro.register('dummy')
class macro_dummy(Macro):
    pass


@Macro.register('recname')
class macro_recname(Macro):
    """recname macro"""

    def process(self, params, rec):
        if params:
            return self.db.view(rec.get(params))
        return self.db.view(params or rec)


    def macro_name(self, params):
        return "Record ID"

@Macro.register('childcount')
class macro_childcount(Macro):
    """childcount macro"""
    keyformat = 'int'

    def preprocess(self, params, recs):
        rectypes = filter(None, params.split(","))
        children = self.db.rel.children([rec.name for rec in recs], recurse=-1)
        # Filter by rectype... somewhat ugly.
        if rectypes:
            allchildren = set()
            for k,v in children.items():
                allchildren |= v
            allg = set()
            for k,v in self.db.record.groupbyrectype(allchildren, rectypes=rectypes).items():
                allg |= v
            for k,v in children.items():
                v &= allg
        
        for rec in recs:
            key = ('rel.children', rec.name, tuple(rectypes))
            self.cache.store(key, len(children.get(rec.name,[])))

    def process(self, params, rec):
        rectypes = filter(None, params.split(","))
        key = ('rel.children', rec.name, tuple(rectypes))
        hit, children = self.cache.check(key)
        if not hit:
            children = self.db.rel.children(rec.name, recurse=-1)
            if rectypes:
                allg = set()
                for k,v in self.db.record.groupbyrectype(children, rectypes=rectypes).items():
                    allg |= v
                children = allg
            self.cache.store(key, len(children))
            return len(children)
        return children

    def macro_name(self, params):
        return "Childcount: %s"%(params)

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
        param, recurse, rectypes = p[0], 1, None
        if len(p) == 3:
            param, recurse, rectypes = p
        elif len(p) == 2:
            param, recurse = p

        recurse = int(recurse or 1)
        parents = self.db.rel.parents(rec.name, recurse=recurse)
        if rectypes:
            p = set()
            for k,v in self.db.record.groupbyrectype(parents, rectypes=rectypes).items():
                p |= v
            parents = p            
        parents = self.db.record.get(parents)
        return filter(None, [i.get(param) for i in parents])

    def macro_name(self, params):
        return "Parent Value: %s"%params

@Macro.register('thumbnail')
class macro_thumbnail(Macro):
    """tile thumb macro"""

    def process(self, params, rec):
        root = "" # emen2.db.config.get('web.root')
        defaults = ["file_binary_image", "thumb", "jpg"]
        params = (params or '').split(",")
        for i,v in enumerate(params):
            if v:
                defaults[i]=v        
        paramdef, size, format = defaults
        
        pd = self.db.paramdef.get(paramdef)
        value = rec.get(pd.name)
        if not value:
            return
        if not pd.iter:
            value = [value]
        ret = []
        for bdo in self.db.binary.get(value):
            if not bdo:
                return Markup("Error getting binary: %s"%value)
            i = Markup("""download/%s/%s?size=%s&format=%s""")%(
                    bdo.name,
                    bdo.filename,
                    size,
                    format
                )
            ret.append(i)
        return ret
        # return "".join(ret)

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


__version__ = "$Revision: 1.77 $".split(":")[1][:-1].strip()