# $Id$
"""Vartypes (data types)

Classes:
    Vartype
    vt_*: A number of built-in data types

"""

import operator
import collections
import urllib
import re

# Escape HTML
import htmlentitydefs
import cgi

# Working with time is fun..
import time
import calendar
import datetime

# ... dateutil helps.
import dateutil
import dateutil.parser
import dateutil.tz
import dateutil.rrule

try:
    import markdown2 as markdown
except ImportError:
    try:
        import markdown
    except ImportError:
        markdown = None

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

def update_username_cache(cache, db, values, lnf=False):
    # Check cache
    to_cache = []
    for v in values:
        key = cache.get_cache_key('displayname', v)
        hit, dn = cache.check_cache(key)
        if not hit:
            to_cache.append(v)

    if to_cache:
        users = db.user.get(to_cache)
        for user in users:
            user.getdisplayname(lnf=lnf)
            key = cache.get_cache_key('displayname', user.name)
            cache.store(key, user.displayname)



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
    '''Base class for vartypes
    
    render
    validate
    reindex
    '''

    #: The index key type for this class
    keyformat = 's'

    #: Is this vartype iterable?
    iterable = True
    
    #: Sort using rendered values?
    sort_render = False

    #: The element to use when rendering as HTML
    elem = 'span'

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
        keytype = keytype or self.vartype
        key = self.cache.get_cache_key('%s.names'%keytype)
        hit, found = self.cache.check_cache(key)
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
                emen2.db.log.warn("Validation: Could not find, but allowing: %s %s (parameter %s)"%(self.vartype, i, self.pd.name))
                ret.append(i)
            else:
                raise ValidationError, "Could not find: %s %s (parameter %s)"%(self.vartype, i, self.pd.name)
        
        if changed:
            self.cache.store(key, found)    
        return ret

    def _rci(self, value):
        """If the parameter is non-iterable, return a single value."""
        if value and not self.pd.iter:
            return value.pop()
        return value or None


    ##### Indexing #####

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
        """Render."""
        if value is None:
            return ''
        if self.pd.iter:
            return ", ".join([unicode(i) for i in value])
        return unicode(value)


@Vartype.register('none')
class vt_none(Vartype):
    pass
    
    
# Float vartypes
#    Indexed as 'f'
@Vartype.register('float')
class vt_float(Vartype):
    """Floating-point number."""

    keyformat = 'f'

    def validate(self, value):
        return self._rci(map(float, ci(value)))

    def render(self, value):
        if value is None:
            return ''
        u = self.pd.defaultunits or ''
        if self.pd.iter:
            return ", ".join(('%g %s'%(i,u) for i in value))
        return '%g %s'%(value, u)


@Vartype.register('percent')
class vt_percent(Vartype):
    """Percentage. 0 <= x <= 1."""

    keyformat = 'f'

    def validate(self, value):
        value = map(float, ci(value))
        for i in value:
            if not 0 <= i <= 1.0:
                raise ValidationError, "Range for percentage is 0 <= value <= 1.0; value was: %s"%i
        return self._rci(value)

    def render(self, value):
        if value is None:
            return ''
        if self.pd.iter:
            return ", ".join(('%0.0f'%(i*100.0) for i in value))
        return '%0.0f'%(i*100.0)



# Integer vartypes
#    Indexed as 'd'
@Vartype.register('int')
class vt_int(Vartype):
    """Integer."""

    keyformat = 'd'

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

    keyformat = 'd'

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




# String vartypes
#    Indexed as keyformat 's'
@Vartype.register('string')
class vt_string(Vartype):
    """String."""

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



@Vartype.register('recorddef')
class vt_recorddef(vt_string):
    """RecordDef name."""

    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='recorddef')
        return self._rci(value)



@Vartype.register('text')
class vt_text(vt_string):
    """Freeform text, with word indexing."""

    elem = 'div'
    unindexed_words = set(["in", "of", "for", "this", "the", "at", "to", "from", "at", "for", "and", "it", "or"])

    def reindex(self, items):
        """(Internal) calculate param index updates for vartype == text"""
        addrefs = collections.defaultdict(list)
        delrefs = collections.defaultdict(list)
        for item in items:
            if item[1]==item[2]:
                continue

            for i in self._reindex_getindexwords(item[1]):
                addrefs[i].append(item[0])

            for i in self._reindex_getindexwords(item[2]):
                delrefs[i].append(item[0])

        allwords = set(addrefs.keys() + delrefs.keys()) - set(self.unindexed_words)
        addrefs2 = {}
        delrefs2 = {}

        for i in allwords:
            # make set, remove unchanged items
            addrefs2[i] = set(addrefs.get(i,[]))
            delrefs2[i] = set(delrefs.get(i,[]))
            u = addrefs2[i] & delrefs2[i]
            addrefs2[i] -= u
            delrefs2[i] -= u

        return addrefs2, delrefs2


    _reindex_getindexwords_m = re.compile('([a-zA-Z]+)|([0-9][.0-9]+)')
    def _reindex_getindexwords(self, value, ctx=None, txn=None):
        """(Internal) Split up a text param into components"""
        if value == None: return []
        value = unicode(value).lower()
        return set((x[0] or x[1]) for x in self._reindex_getindexwords_m.findall(value))




# Time vartypes (keyformat is string)
#    Indexed as keyformat 's'
@Vartype.register('datetime')
class vt_datetime(vt_string):
    """ISO 8601 Date time."""

    def validate(self, value):
        ret = []
        for i in ci(value):
            if i:
                t = dateutil.parser.parse(i)
                if not t.tzinfo:
                    raise ValidationError, "No UTC offset: %s"%i
                ret.append(t.isoformat())
        return self._rci(ret)


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

    elem = "time"

    def validate(self, value):
        ret = []
        for i in ci(value):
            i = parse_iso8601(i, result='time')
            if i:
                ret.append(i)
        return self._rci(ret)






# Reference vartypes.
#    Indexed as keyformat 's'
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
        
    def render(self, value):
        if value is None:
            return ''
        return ", ".join(('%s: %s'%(k, v) for k,v in value.items()))


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

    def render(self, value):
        value = ci(value)
        try:
            v = self.db.binary.get(value)
            value = [i.filename for i in v]
        except (ValueError, TypeError), e:
            value = ['Error getting binary: %s'%(i) for i in value]
        return ", ".join(value)




# md5 checksum
#    Indexed as keyformat 's'
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

    # This ma change in the future
    keyformat = 'd'

    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='record')
        return self._rci(value)


@Vartype.register('link')
class vt_link(Vartype):
    """Reference."""

    def validate(self, value):
        value = self._validate_reference(ci(value), keytype=self.cache.keytype) # Ugly hack :(
        return self._rci(value)



# User, ACL, and Group vartypes
#    Indexed as keyformat 's'
@Vartype.register('user')
class vt_user(Vartype):
    """Users."""
    
    def validate(self, value):
        value = self._validate_reference(ci(value), keytype='user')
        return self._rci(value)

    def render(self, value):
        value = ci(value)
        update_username_cache(self.cache, self.db, value, lnf=self.options.get('lnf'))
        lis = []
        for i in value:
            key = self.cache.get_cache_key('displayname', i)
            hit, dn = self.cache.check_cache(key)
            lis.append(dn or '')
        return ", ".join(lis)


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


    def render(self, value):
        if not value:
            return ''
        allusers = reduce(lambda x,y:x+y, value)
        unames = {}
        for user in self.db.user.get(allusers):
            unames[user.name] = user.displayname

        levels = ["Read","Comment","Write","Owner"]
        ret = []
        for level, names in zip(levels, value):
            namesr = [unames.get(i,"(%s)"%i) for i in names]
            if namesr:
                ret.append("%s: %s"%(level, ", ".join(namesr)))
        return ', '.join(ret)


    def reindex(self, items):
        """(Internal) Calculate secrindex updates"""
        # Calculating security updates...
        addrefs = collections.defaultdict(list)
        delrefs = collections.defaultdict(list)
        for name, new, old in items:
            #nperms = set(reduce(operator.concat, new or [], []))
            #operms = set(reduce(operator.concat, old or [], []))
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

    def render(self, value):
        value = ci(value)
        users = [i[0] for i in value]
        update_username_cache(self.cache, self.db, users)
        lis = []
        for user, time, comment in value:
            key = self.cache.get_cache_key('displayname', user)
            hit, dn = self.cache.check_cache(key)
            t = '%s @ %s: %s\n'%(user, time, comment)
            lis.append(t)
        return ", ".join(lis)


@Vartype.register('history')
class vt_history(Vartype):
    """History."""
    
    keyformat = None

    def render(self, value):
        value = ci(value)
        users = [i[0] for i in value]
        update_username_cache(self.cache, self.db, users)
        lis = []
        for user, time, parameter, oldvalue in value:
            key = self.cache.get_cache_key('displayname', user)
            hit, dn = self.cache.check_cache(key)
            t = '%s @ %s: changed %s\n'%(user, time, parameter)
            lis.append(t)
        return ", ".join(lis)



__version__ = "$Revision$".split(":")[1][:-1].strip()
