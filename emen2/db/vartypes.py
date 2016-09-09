# $Id: vartypes.py,v 1.162 2013/06/23 06:49:18 irees Exp $
"""Vartypes (data types)

Classes:
    Vartype
    vt_*: A number of built-in data types

"""

import operator
import collections
import urllib
import re

# Working with time is even more fun.
import time
import calendar
import datetime

# ... dateutil helps.
import dateutil
import dateutil.parser
import dateutil.tz
import dateutil.rrule

# Markdown and Markupsafe are required now.
import markdown
from markupsafe import Markup, escape

# EMEN2 imports
import emen2.db.log
import emen2.db.exceptions
import emen2.util.listops

# Convenience
tzutc = dateutil.tz.tzutc()
ci = emen2.util.listops.check_iterable
ValidationError = emen2.db.exceptions.ValidationError

# Allow references to missing items.
ALLOW_MISSING = True

# Text values equivalent to "None"
NONEVALUES = [None, "", "N/A", "n/a", "None"]

##### Helper methods #####

def update_user_cache(cache, db, values):
    # Check cache
    to_cache = []
    for v in values:
        hit, dn = cache.check(('user', v))
        if not hit:
            to_cache.append(v)

    if to_cache:
        users = db.user.get(to_cache)
        for user in users:
            cache.store(('user', user.name), user)

def update_recorddef_cache(cache, db, values):
    to_cache = []
    for v in values:
        hit, dn = cache.check(('recorddef', v))
        if not hit:
            to_cache.append(v)

    if to_cache:
        rds = db.recorddef.get(to_cache)
        for rd in rds:
            cache.store(('recorddef', rd.name), rd)
    



def iso8601duration(d):
    """
    Parse ISO 8601 duration format.

    From Wikipedia, ISO 8601 duration format is:
        P[n]Y[n]M[n]DT[n]H[n]M[n]S

    P is the duration designator (historically called "period") placed at the start of the duration representation.
    Y is the year designator that follows the value for the number of years.
    M is the month designator that follows the value for the number of months.
    W is the week designator that follows the value for the number of weeks.
    D is the day designator that follows the value for the number of days.
    T is the time designator that precedes the time components of the representation.
    H is the hour designator that follows the value for the number of hours.
    M is the minute designator that follows the value for the number of minutes.
    S is the second designator that follows the value for the number of seconds.

    Examples:
    d = 'P1M2D' # 1 month, 2 days
    d = 'P1Y2M3DT4H5M6S' # 1 year, 2 months, 3 days, 4 hours, 5 minutes, 6 seconds
    d = 'P3W' # 3 weeks

    """

    regex = re.compile("""
            (?P<type>.)
            ((?P<weeks>[0-9,]+)W)?
            ((?P<years>[0-9,]+)Y)?
            ((?P<months>[0-9,]+)M)?
            ((?P<days>[0-9,]+)D)?
            (T
                ((?P<hours>[0-9,]+)H)?
                ((?P<minutes>[0-9,]+)M)?
                ((?P<seconds>[0-9,]+)S)?
            )?
            """, re.X)
    match = regex.search(d)
    rd = {} # return date

    # rdate['type'] = match.group('type')
    for key in ['weeks','years','months','days','hours','minutes','seconds']:
        if match.group(key):
            rd[key] = int(match.group(key))

    return rd


##### Vartypes #####

class Vartype(object):
    '''Base class for Vartypes.'''

    #: The index key type for this class
    keyformat = 'str'

    #: Is this vartype iterable?
    iterable = True
    
    #: Sort using rendered values?
    sort_render = False

    def __init__(self, pd=None, cache=None, db=None, options=None):
        self.pd = pd
        self.cache = cache
        self.db = db
        self.options = options or {}

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
    def get_vartype(cls, name, *args, **kwargs):
        return cls.registered[name](*args, **kwargs)


    ##### Validation #####

    # def validate(self, pd, value):
    #     if value in NONEVALUES:
    #         return None
    # 
    #     if pd.property:
    #         value = self.properties[pd.property]().validate(self, pd, value, self.db)
    # 
    #     return self.vartypes[pd.vartype](cache=self.cache, db=self.db, pd=pd).validate(value)

    def validate(self, value):
        """Validate a value"""
        raise ValidationError, "%s is an organizational parameter, and is not intended to be used."%self.pd.name

    def _validate_reference(self, value, keytype=None):
        ret = []
        changed = False
        key = ('%s.names'%keytype,)
        hit, found = self.cache.check(key)
        if not hit:
            found = set()
            changed = True

        for i in value:       
            i = self.db._db.dbenv[keytype].keyclass(i) # ugly hack :(
            if i in found:
                ret.append(i)
            elif self.db.exists(i, keytype=keytype):
                ret.append(i)
                found.add(i)
                changed = True
            elif ALLOW_MISSING:
                emen2.db.log.warn("Validation: Could not find, but allowing: %s (parameter %s)"%(i, self.pd.name))
                ret.append(i)
            else:
                raise ValidationError, "Could not find: %s (parameter %s)"%(i, self.pd.name)
        
        if changed:
            self.cache.store(key, found)    
        return ret

    def _rci(self, value):
        """If the parameter is non-iterable, return a single value."""
        if value and not self.pd.iter:
            return value.pop()
        return value or None

    
    ##### Indexing #####

    def reindex_keywords(self, items):
        return {}, {}

    def reindex(self, items):
        addrefs = collections.defaultdict(set)
        delrefs = collections.defaultdict(set)
        for name, new, old in items:
            if new == old:
                continue
            if not self.pd.iter:
                new=[new]
                old=[old]

            new = set(new or [])
            old = set(old or [])
            for n in new-old:
                addrefs[n].add(name)
            for o in old-new:
                delrefs[o].add(name)

        if None in addrefs:
            del addrefs[None]
        if None in delrefs:
            del delrefs[None]

        return addrefs, delrefs


    ##### Rendering #####

    def process(self, value):
        return value

    def render(self, value):
        output = self.options.get('output', 'unicode')
        r = self.render_unicode
        if output == "html":
            r = self.render_html
        elif output == "form":
            r = self.render_form
        return r(value)

    def render_unicode(self, value):
        """Render unicode values."""
        if value is None:
            return ''
        if self.pd.iter:
            return ", ".join(self._unicode(i) for i in value)
        return self._unicode(value)
    
    def render_html(self, value):
        """Render HTML formatted values. All values MUST be escaped."""
        if value is None:
            return ''
        if self.pd.iter:
            return self._li_wrap([self._html(i) for i in value])
        return self._html(value)

    def render_form(self, value):
        if self.pd.immutable:
            return self._html(value)
        if self.pd.iter:
            elem = self._li_wrap(
                [self._form(i) for i in (value or [])],
                hidden=self._form(None),
                add=self._add()
                )
        else:
            elem = self._form(value)
        return elem

    def _unicode(self, value):
        return unicode(value)
    
    def _html(self, value):
        if value is None:
            return ''
        elem = Markup("""<span class="e2-edit" data-paramdef="%s">%s</span>""")%(self.pd.name, self._unicode(value))
        return elem
        
    def _form(self, value):
        if value is None:
            value = ''
        elem = Markup("""<span class="e2-edit" data-paramdef="%s" data-vartype="%s"><input type="text" name="%s" value="%s" /></span>""")%(
            self.pd.name,
            self.pd.vartype,
            self.pd.name,
            value
        )
        return elem

    def _add(self):
        return """<input type="button" value="+" class="e2-edit-add" />"""

    def _li_wrap(self, values, hidden=None, add=None):
        lis = ["""<li>%s</li>"""%value for value in values]
        if hidden:
            lis.append("""<li class="e2-edit-template e2l-hide">%s</li>"""%hidden)            
        if add:
            lis.append("""<li>%s</li>"""%add)
        return """<ul>%s</ul>"""%"".join(lis)
        


@Vartype.register('none')
class vt_none(Vartype):
    pass
    

# Float vartypes
#    Indexed as 'f'
@Vartype.register('float')
class vt_float(Vartype):
    """Floating-point number."""

    keyformat = 'float'

    def validate(self, value):
        return self._rci(map(float, ci(value)))

    def _unicode(self, value):
        u = self.pd.defaultunits or ''
        return '%g %s'%(value, u)

    def _form(self, value):    
        if value is None:
            value = ''
        units = self.pd.defaultunits or ''
        return Markup("""<span class="e2-edit" data-paramdef="%s" data-vartype="%s"><input type="text" name="%s" value="%s" /> %s</span>""")%(
            self.pd.name,
            self.pd.vartype,
            self.pd.name,
            value,
            units
        )
    

@Vartype.register('percent')
class vt_percent(Vartype):
    """Percentage. 0 <= x <= 1."""

    keyformat = 'float'

    def validate(self, value):
        value = map(float, ci(value))
        for i in value:
            if not 0 <= i <= 1.0:
                raise ValidationError, "Range for percentage is 0 <= value <= 1.0; value was: %s"%i
        return self._rci(value)

    def _unicode(self, value):
        return '%0.0f'%(i*100.0)



# Integer vartypes
#    Indexed as 'd'
@Vartype.register('int')
class vt_int(Vartype):
    """Integer."""

    keyformat = 'int'

    def validate(self, value):
        return self._rci(map(int, ci(value)))


@Vartype.register('coordinate')
class vt_coordinate(Vartype):
    """Coordinates; tuples of floats."""

    keyformat = None

    def validate(self, value):
        return [(float(x), float(y)) for x,y in ci(value)]


@Vartype.register('boolean')
class vt_boolean(Vartype):
    """Boolean value. Accepts 0/1, True/False, T/F, Yes/No, Y/N, None."""

    keyformat = 'int'

    def validate(self, value):
        t = ['t', 'y', 'yes', 'true', '1']
        f = ['f', 'n', 'no', 'false', 'none', '0']
        ret = []
        for i in ci(value):
            i = unicode(value).lower()
            if i in t:
                i = True
            elif i in f:
                i = False
            else:
                raise ValidationError, "Invalid boolean: %s"%unicode(value)
            ret.append(i)
        return self._rci(ret)

    def _form(self, value):
        choices = []
        if value is None:
            choices.append("""<option value="" checked="checked" />""")
            choices.append("""<option>True</option>""")
            choices.append("""<option>False</option>""")
        elif value:
            choices.append("""<option value="" />""")
            choices.append("""<option checked="checked">True</option>""")
            choices.append("""<option>False</option>""")
        else:
            choices.append("""<option value="" />""")
            choices.append("""<option>True</option>""")
            choices.append("""<option checked="checked" >False</option>""")
        return Markup("""<span class="e2-edit" data-paramdef="%s" data-vartype="%s"><select>%s</select></span>""")%(
            self.pd.name, 
            self.pd.vartype,
            Markup("".join(choices))
            )
        

@Vartype.register('keywords')
class vt_keywords(Vartype):
    pass


# String vartypes
#    Indexed as keyformat 'str'
@Vartype.register('string')
class vt_string(Vartype):
    """String."""
    
    _indexwords = re.compile('[a-zA-Z0-9-]{3,}')

    def _getindexwords(self, value):
        """(Internal) Split up a text param into components"""
        # print "-> reindex", self.pd.name, self.pd.vartype, self._indexwords.findall(value)
        if value == None: return set()
        value = unicode(value).lower()
        return set(x for x in self._indexwords.findall(value))

    def reindex_keywords(self, items):
        addrefs = collections.defaultdict(list)
        delrefs = collections.defaultdict(list)
        for item in items:
            if item[1]==item[2]:
                continue
            for i in self._getindexwords(item[1]):
                addrefs[i].append(item[0])
            for i in self._getindexwords(item[2]):
                delrefs[i].append(item[0])

        allwords = set(addrefs.keys() + delrefs.keys())
        addrefs2 = {}
        delrefs2 = {}
        for i in allwords:
            addrefs2[i] = set(addrefs.get(i,[]))
            delrefs2[i] = set(delrefs.get(i,[]))
            u = addrefs2[i] & delrefs2[i]
            addrefs2[i] -= u
            delrefs2[i] -= u
        return addrefs2, delrefs2

    def validate(self, value):
        return self._rci([unicode(x).strip() for x in ci(value)])


@Vartype.register('choice')
class vt_choice(vt_string):
    """One value from a defined list of choices."""

    def validate(self, value):
        value = [unicode(i).strip() for i in ci(value)]
        for v in value:
            if v not in self.pd.choices:
                raise ValidationError, "Invalid choice: %s"%v
        return self._rci(value)

    def _form(self, value):
        choices = []
        if value is None:
            value = ''
        for choice in ['']+self.pd.choices:
            if choice == value:
                elem = Markup("""<option value="%s" selected="selected">%s</option>""")%(choice, choice)
            else:
                elem = Markup("""<option value="%s">%s</option>""")%(choice, choice)
            choices.append(elem)
            
        return Markup("""<span class="e2-edit" data-paramdef="%s" data-vartype="%s"><select name="%s">%s</select></span>""")%(
            self.pd.name,
            self.pd.vartype,
            self.pd.name,
            Markup("".join(choices))
            )
        

@Vartype.register('text')
class vt_text(vt_string):
    """Freeform text, with word indexing."""

    elem = 'div'

    def reindex(self, items):
        return self.reindex_keywords(items)

    def _html(self, value):
        if value is None:
            return ''
        value = Markup(markdown.markdown(unicode(value), safe_mode='escape'))
        elem = Markup("""<div class="e2-edit" data-paramdef="%s">%s</div>""")%(self.pd.name, value)
        return elem

    def _form(self, value):
        if value is None:
            value = ''
        return Markup("""<div class="e2-edit" data-paramdef="%s" data-vartype="%s"><textarea name="%s">%s</textarea></div>""")%(
            self.pd.name,
            self.pd.vartype,
            self.pd.name,
            value
            )



# Time vartypes (keyformat is string)
#    Indexed as keyformat 'str'
import dateutil.parser
import dateutil.tz

@Vartype.register('datetime')
class vt_datetime(Vartype):
    """ISO 8601 Date time."""

    fmt = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y-%m-%d',
        '%Y-%m',
        '%Y'
    ]

    def validate(self, value):
        ret = []
        for i in ci(value):
            if i:
                t = dateutil.parser.parse(i)
                if not t.tzinfo:
                    raise ValidationError, "No UTC offset: %s"%i
                ret.append(t.isoformat())
        return self._rci(ret)
        
    def _strip(self, t, time_precision=None):
        limit = time_precision or self.options.get('time_precision') or 0
        for prec, i in enumerate((t.microsecond, t.second, t.minute, t.hour, t.day, t.month, t.year)):
            if i == 0:
                prec += 1
            else:
                break
        if prec < limit:
            prec = limit
        try:
            return t.strftime(self.fmt[prec])
        except:
            return "Date out of bounds! %s"%value
    
    def _unicode(self, value):
        tz = self.options.get('tz')
        raw_time = dateutil.parser.parse(value)
        local_time = raw_time.astimezone(dateutil.tz.gettz(tz))
        return self._strip(local_time)
    
    def _html(self, value):
        tz = self.options.get('tz')
        raw_time = dateutil.parser.parse(value)
        raw_utc = raw_time.astimezone(dateutil.tz.gettz())
        local_time = raw_time.astimezone(dateutil.tz.gettz(tz))
        return Markup("""<time class="e2-edit" data-paramdef="%s" datetime="%s" title="Raw value: %s \nUTC time: %s \nLocal time: %s">%s</time>""")%(
            self.pd.name,
            raw_time.isoformat(),
            value,
            raw_utc.isoformat(),
            local_time.isoformat(),
            self._strip(local_time)
            )
            

@Vartype.register('date')
class vt_date(vt_datetime):
    """Date, yyyy-mm-dd."""
    def validate(self, value):
        ret = []
        for i in ci(value):
            i = parse_iso8601(i, result='date')
            if i:
                ret.append(i)
        return self._rci(ret)


@Vartype.register('time')
class vt_time(vt_datetime):
    """Time, HH:MM:SS."""
    def validate(self, value):
        ret = []
        for i in ci(value):
            i = parse_iso8601(i, result='time')
            if i:
                ret.append(i)
        return self._rci(ret)



# Reference vartypes.
#    Indexed as keyformat 'str'
@Vartype.register('uri')
class vt_uri(Vartype):
    """URI"""

    # ian: todo: parse with urlparse
    def validate(self, value):
        value = [unicode(i).strip() for i in ci(value)]
        for v in value:
            if not v.startswith("http://"):
                raise ValidationError, "Invalid URI: %s"%value
        return self._rci(value)



# Mapping types
@Vartype.register('dict')
class vt_dict(Vartype):
    """Dictionary with string keys and values."""

    keyformat = None

    def validate(self, value):
        if not value:
            return None
        r = [(unicode(k), unicode(v)) for k,v in value.items() if k]
        return dict(r)


@Vartype.register('dictlist')
class vt_dictlist(vt_dict):
    """Dictionary with string keys and list values."""

    keyformat = None

    def validate(self, value):
        if not value:
            return None        
        ret = {}
        for k,v in value.items():
            k = unicode(k)
            v = [unicode(i) for i in v]
            ret[k] = v
        return ret


# Binary vartypes
#    Not indexed.
@Vartype.register('binary')
class vt_binary(Vartype):
    """File Attachment"""

    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='binary')
        return self._rci(value)

    def _unicode(self, value):
        try:
            v = self.db.binary.get(value)
            return v.filename or value
        except (ValueError, TypeError, AttributeError, KeyError), e:
            return "Error getting binary: %s"%value

    def _add(self):
        label = "Change"
        multiple = ""
        if self.pd.iter:
            label = "Add attachments"
            multiple = "multiple"
        return Markup("""%s <input type="file" name="%s" multiple="%s" />""")%(
            label,
            self.pd.name,
            multiple
            )
            
    def _html(self, value):
        if value is None:
            return ''
        bdo = self.db.binary.get(value)
        elem = Markup("""
            <span class="e2-edit" data-paramdef="%s">
                <a href="/download/%s/%s">
                    <img class="e2l-thumbnail" src="/download/%s/%s?size=thumb&format=jpg" alt="Thumb" />
                    %s
                </a>
            </span>
            """)%(
                self.pd.name,
                bdo.name,
                bdo.filename,
                bdo.name,
                bdo.filename,
                bdo.filename
            )
        return elem

    def _form(self, value):
        elem = ""       
        if value:
            bdo = self.db.binary.get(value)
            if not bdo:
                return Markup("Error getting binary: %s"%value)
            src = "/download/%s/thumb.jpg?size=thumb"%(bdo.name)        
            elem = Markup("""
                <div class="e2-infobox" data-name="%s" data-keytype="user">
                    <input type="checkbox" name="%s" value="%s" checked="checked" />
                    <img src="%s" class="e2l-thumbnail" alt="Photo" />
                    <h4>%s</h4>
                    <p class="e2l-small">%s</p>                
                </div>""")%(
                    bdo.name,
                    self.pd.name,
                    bdo.name,
                    src,
                    bdo.filename,
                    bdo.filesize
                )
        
        # Show a 'Change' button...
        if not self.pd.iter:
            elem += self._add()
            
        return Markup("""<div class="e2-edit" %s>%s</div>""")%(
            self.pd.name,
            elem
            )



# md5 checksum
#    Indexed as keyformat 'str'
@Vartype.register('md5')
class vt_md5(Vartype):
    """String"""

    def validate(self, value):
        return self._rci([unicode(x).strip() for x in ci(value)])



# References to other database objects
#    Not indexed.
@Vartype.register('record')
class vt_record(Vartype):
    """References to other Records."""

    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='record')
        return self._rci(value)


@Vartype.register('link')
class vt_link(Vartype):
    """Reference."""
    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='record') # Ugly hack :(
        return self._rci(value)


@Vartype.register('recorddef')
class vt_recorddef(Vartype):
    """RecordDef name."""

    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='recorddef')
        return self._rci(value)

    def _unicode(self, value):
        update_recorddef_cache(self.cache, self.db, [value])
        key = ('recorddef', value)
        hit, rd = self.cache.check(key)
        if rd:
            return rd.desc_short
        return value



# User, ACL, and Group vartypes
#    Indexed as keyformat 'str'
@Vartype.register('user')
class vt_user(Vartype):
    """Users."""
    
    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='user')
        return self._rci(value)

    def _unicode(self, value):
        update_user_cache(self.cache, self.db, [value])
        key = ('user', value)
        hit, user = self.cache.check(key)
        if user:
            return user.getdisplayname(lnf=self.options.get('lnf'))
        return value

    def _add(self):
        label = "Change"
        iter_ = ""
        if self.pd.iter:
            label = "+"
            iter_ = "true"
        return Markup("""<input type="button" value="%s" class="e2-edit-add-find" data-keytype="user" data-param="%s" data-iter="%s"/>""")%(
            label,
            self.pd.name,
            iter_
            )

    def _form(self, value):
        if value is None:
            return ""

        update_user_cache(self.cache, self.db, [value])
        key = ('user', value)
        hit, user = self.cache.check(key)

        src = "/static/images/user.png"
        if user.userrec.get('person_photo'):
            src = "/download/%s/user.jpg?size=thumb"%(user.userrec.get('person_photo'))

        elem = Markup("""
            <div class="e2-infobox" data-name="%s" data-keytype="user">
                <input type="checkbox" name="%s" value="%s" checked="checked" />
                <img src="%s" class="e2l-thumbnail" alt="Photo" />
                <h4>%s</h4>
                <p class="e2l-small">%s</p>                
            </div>
            """)%(
                value,
                self.pd.name,
                value,
                src,
                user.getdisplayname(),
                user.email
            )
        
        # Show a 'Change' button...
        if not self.pd.iter:
            elem += self._add()
            
        return Markup("""<div class="e2-edit" data-paramdef="%s" data-vartype="%s">%s</div>""")%(
            self.pd.name,
            self.pd.vartype,
            elem
            )
        

@Vartype.register('acl')
class vt_acl(Vartype):
    """Permissions access control list; nested lists of users."""
    
    def validate(self, value):
        if not hasattr(value, '__iter__'):
            value = [[value],[],[],[]]

        if hasattr(value, 'items'):
            v = [[],[],[],[]]
            ci = emen2.util.listops.check_iterable
            v[0] = ci(value.get('read'))
            v[1] = ci(value.get('comment'))
            v[2] = ci(value.get('write'))
            v[3] = ci(value.get('admin'))
            value = v

        for i in value:
            if not hasattr(i, '__iter__'):
                raise ValidationError, "Invalid permissions format: %s"%(value)

        value = [[unicode(y) for y in x] for x in value]
        if len(value) != 4:
            raise ValidationError, "Invalid permissions format: ", value

        users = reduce(lambda x,y:x+y, value)
        self._validate_reference(users, keytype='user')
        return value

    def reindex(self, items):
        addrefs = collections.defaultdict(list)
        delrefs = collections.defaultdict(list)
        for name, new, old in items:
            nperms = set()
            for i in new or []:
                nperms |= set(i)
            operms = set()
            for i in old or []:
                operms |= set(i)

            for user in nperms - operms:
                addrefs[user].append(name)

            for user in operms - nperms:
                delrefs[user].append(name)

        return addrefs, delrefs

    def _form(self, value):
        return self._html(value)


@Vartype.register('group')
class vt_group(Vartype):
    """Group."""
    
    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='group')
        return self._rci(value)


# Comment and History vartypes
#    Not indexed
@Vartype.register('comments')
class vt_comments(Vartype):
    """Comments."""
    
    keyformat = None

    # ian: todo... sort this out.
    def validate(self, value):
        return value
      
    def _html(self, value):
        user, dt, comment = value
        update_user_cache(self.cache, self.db, [user])
        key = ('user', user)
        hit, user = self.cache.check(key)
        return Markup("""%s said on <time class="e2-localize" datetime="%s">%s</time>: %s""")%(
                user.getdisplayname(),
                dt,
                dt,
                comment
            )

    def render_form(self, value):
        return Markup("""<div class="e2-edit" data-paramdef="%s" data-vartype="%s"><textarea placeholder="Add additional comments"></textarea></div>""")%(self.pd.name, self.pd.vartype)



@Vartype.register('history')
class vt_history(Vartype):
    """History."""
    
    keyformat = None




__version__ = "$Revision: 1.162 $".split(":")[1][:-1].strip()
