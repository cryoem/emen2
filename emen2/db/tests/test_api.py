#!/usr/bin/env python
import collections
import random
import string
import inspect
import tempfile
import shutil

def randword(length):
    s = string.lowercase + string.digits
    return ''.join(random.sample(s,length))

EMAIL = '%s@sierra.example.com'%randword(10)
PASSWORD = randword(10)


######################################
from emen2.db.exceptions import *
class ExpectException(Exception):
    pass

class RunTests(object):
    __tests = collections.OrderedDict()
    __counter = 1
    def __init__(self, db=None):
        self.db = db
        
    @classmethod
    def test(cls, f):
        f.counter = cls.__counter
        cls.__counter += 1
        return f
    
    @classmethod
    def register(cls, c):
        cls.__tests[c.__name__] = c

    def run(self):
        for k,c in self.__tests.items():
            c(db=self.db).run()
    
    def runone(self, k=None, cls=None):
        if k:
            cls = self.__tests[k]
        cls(db=self.db).run()

    def coverage(self):
        for k,c in self.__tests.items():
            print c(db=self.db)._tests()
        

register = RunTests.register
test = RunTests.test

class Test(object):
    children = []
    def __init__(self, db=None):
        self.db = db

    def _tests(self):
        methods = [f for k,f in inspect.getmembers(self, predicate=inspect.ismethod) if getattr(f, 'counter', None)]    
        methods = sorted(methods, key=lambda f:getattr(f, 'counter', None))
        return methods
        
    
    def header(self, *msg):
        print "\n====== "+" ".join(map(unicode, msg)) + " ======"
    
    def msg(self, *msg, **kwargs):
        if 'newline' not in kwargs:
            kwargs['newline'] = True
        if kwargs.get('newline'):
            print
        print "\t"+" ".join(map(unicode, msg))

    def ok(self, *msg):
        self.msg("ok:", *msg, newline=False)

    def fail(self, *msg):
        self.msg("FAILED:", *msg)

    def setup(self):
        pass

    def run(self):
        self.header("Setup:", self)
        with self.db:
            self.setup()
        for method in self._tests():
            self.header(method)
            with self.db:
                method()
        for c in self.children:
            t = c(db=self.db)
            t.run()
            
######################################
        
# @register
class Create(Test):
    def run(self):
        emen2.db.database.setup(db=self.db, rootpw=PASSWORD)

@register
class Time(Test):
    @test
    def api_time_now(self):
        self.db.time.now()

    @test
    def api_time_difference(self):
        self.db.time.difference('2013-01-01')

@register
class Version(Test):
    @test
    def api_version(self):
        self.db.version()

@register
class Ping(Test):
    @test
    def api_ping(self):
        self.db.ping()
    
######################################

@register
class NewUser(Test):
    @test
    def api_newuser_new(self):
        email = '%s@yosemite.exmaple.com'%randword(10)
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        return user

    @test
    def api_newuser_request(self):
        user = self.db.newuser.request(self.api_newuser_new())
        return user

    @test
    def api_newuser_approve(self):
        user = self.api_newuser_request()
        self.db.newuser.approve(user.name)

    @test
    def api_newuser_reject(self):
        user = self.api_newuser_request()
        self.db.newuser.reject(user.name)

@register
class User(Test):
    def setup(self):
        # Create account        
        email = '%s@yosemite.exmaple.com'%randword(10)
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='John', name_last='Muir')
        user = self.db.newuser.request(user)
        self.db.newuser.approve(user.name)
        self.email = email
        self.password = password
        self.username = user.name
        
    @test
    def api_user_get(self):
        user = self.db.user.get(self.username)
        # Check filt=False
        try:
            self.db.user.get('fail', filt=False)
        except KeyError:
            pass
        return user

    @test
    def api_user_put(self):
        user = self.db.user.get(self.username)
        user['name_first'] = "Test"
        self.db.user.put(user)
        # Reset state
        user = self.db.user.get(self.username)
        user['name_first'] = "John"
        self.db.user.put(user)

    @test
    def api_user_filter(self):
        self.db.user.filter()

    @test
    def api_user_find(self):
        self.db.user.find("John")

    @test
    def api_user_setprivacy(self):
        self.db.user.setprivacy(self.username, 0)
        assert self.db.user.get(self.username).privacy == 0
        self.db.user.setprivacy(self.username, 1)
        assert self.db.user.get(self.username).privacy == 1
        self.db.user.setprivacy(self.username, 2)
        assert self.db.user.get(self.username).privacy == 2
        # Reset state
        self.db.user.setprivacy(self.username, 0)

    @test
    def api_user_disable(self):
        self.db.user.disable(self.username)
        assert self.db.user.get(self.username).disabled == True
        # Reset state
        self.db.user.enable(self.username)
        assert self.db.user.get(self.username).disabled == False

    @test
    def api_user_enable(self):
        self.db.user.enable(self.username)
        assert self.db.user.get(self.username).disabled == False

    @test
    def api_user_setpassword(self):
        # Change password, and make sure we can login.
        newpassword = self.password[::-1]        
        self.db.user.setpassword(self.username, newpassword, password=self.password)
        self.db.auth.login(self.username, newpassword)
        # Reset state
        self.db.user.setpassword(self.username, self.password, password=newpassword)
        self.db.auth.login(self.username, self.password)

    @test
    def api_user_setemail(self):
        # Change email, and make sure email index is updated for login.
        email = '%s@change.example.com'%randword(10)
        self.db.user.setemail(self.username, email, password=self.password)
        self.db.auth.login(email, self.password)
        # Reset state
        self.db.user.setemail(self.username, self.email, password=self.password)
        self.db.auth.login(self.email, self.password)

    @test
    def api_user_resetpassword(self):
        try:
            self.db.user.resetpassword(self.username)
        except emen2.db.exceptions.EmailError: 
            return
        # Get secret.
        user = self.db._db.dbenv['user']._get_data(self.username)
        secret = user.data.get('secret')
        newpassword = self.password[::-1]                
        self.db.user.resetpassword(password=newpassword, secret=secret)
    
    @test
    def api_user_expirepassword(self):
        self.db.user.expirepassword(self.username)

    @test
    def test_change_displayname(self):
        user = self.db.user.get(self.username)
        user.name_first = "Russell"
        user.name_last = "Lee"
        self.db.user.put(user)
        assert self.db.user.get(self.username).displayname == "Russell Lee"
        # users = self.db.user.find("Russell")
        # assert self.username in [i.name for i in users]

    @test
    def test_secret(self):
        pass

######################################

@register
class Group(Test):
    def setup(self):
        # Create some new users
        users = []
        for i in ['Dorothea Lange', 'Walker Evans']:
            name = i.partition(' ')
            email = '%s-%s@wpa.example.com'%(name[2], randword(10))
            user = self.db.newuser.request(dict(email=email, name_first=name[0], name_last=name[2], password=randword(10)))
            self.db.newuser.approve(user.name)
            users.append(user.name)

        group = self.db.group.new(displayname="Farm Security Administration")
        group = self.db.group.put(group)

        self.groupname = group.name
        self.users = users
        
    @test
    def api_group_new(self):
        group = self.db.group.new(displayname="Tennessee Valley Authority")
        return group

    @test
    def api_group_put(self):
        group = self.api_group_new()
        group = self.db.group.put(group)
        return group

    @test
    def api_group_filter(self):
        self.db.group.filter()

    @test
    def api_group_find(self):
        for group in self.db.group.find("Farm"):
            group, group.data
            
    @test
    def test_group_members(self):
        # Add users
        group = self.db.group.get(self.groupname)
        for i in self.users:
            group.adduser(i)
        self.db.group.put(group)
        group = self.db.group.get(self.groupname)
        for i in self.users:
            assert i in group.members()
        
        # Remove a user
        group = self.db.group.get(self.groupname)
        for i in self.users:
            group.removeuser(i)
        self.db.group.put(group)
        group = self.db.group.get(self.groupname)
        for i in self.users:
            assert i not in group.members()

    @test
    def test_group_change_displayname(self):
        group = self.db.group.get(self.groupname)
        orig = group.displayname
        group.displayname = "Department of the Interior"
        self.db.group.put(group)
        groups = self.db.group.find("Interior")
        assert self.groupname in [i.name for i in groups]
        # Revert
        group = self.db.group.get(self.groupname)
        group.displayname = orig
        self.db.group.put(group)    

######################################

@register
class Auth(Test):
    def setup(self):
        # Create account
        email = '%s@moonrise.exmaple.com'%randword(10)
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Ansel', name_last='Adams')
        user = self.db.newuser.request(user)
        self.db.newuser.approve(user.name)
        self.email = email
        self.password = password
        self.username = user.name
            
    @test
    def api_auth_login(self):
        self.db.auth.login(self.username, self.password)

    @test
    def api_auth_check_context(self):
        self.db.auth.check.context()

    @test
    def api_auth_check_admin(self):
        self.db.auth.check.admin()

    @test
    def api_auth_check_create(self):
        self.db.auth.check.create()

    # @test
    # def api_auth_logout(self):
    #     print self.db.auth.logout()
    #     print self.db.auth.login("root", PASSWORD)

######################################

@register
class ParamDef(Test):
    def setup(self):
        pd = self.db.paramdef.new(vartype='float', desc_short='Numerical aperture')
        pd = self.db.paramdef.put(pd)
        self.pdname = pd.name

    @test
    def api_paramdef_new(self):
        self.msg("Checking paramdef.new")
        pd = self.db.paramdef.new(vartype='int', desc_short='Film speed')
        self.ok(pd)

    @test
    def api_paramdef_put(self):
        self.msg("Checking paramdef.put")
        pd = self.db.paramdef.new(vartype='int', desc_short='Film speed')
        pd = self.db.paramdef.put(pd)
        assert pd.name
        assert pd.vartype == 'int'
        assert pd.desc_short == 'Film speed'
        self.ok(pd)

    @test
    def api_paramdef_get(self):
        self.msg("Checking paramdef.get")
        pd = self.db.paramdef.get(self.pdname)
        assert pd.name == self.pdname
        self.ok(pd)

    @test
    def api_paramdef_filter(self):
        pds = self.db.paramdef.filter()
        assert self.pdname in pds
        self.ok()

    @test
    def api_paramdef_find(self):
        pds = self.db.paramdef.find('aperture')
        assert self.pdname in [pd.name for pd in pds]
        self.ok()

    @test
    def api_paramdef_properties(self):
        self.msg("Checking list of properties")
        props = self.db.paramdef.properties()
        self.ok(props)

    @test
    def api_paramdef_units(self):
        self.msg("Checking list of units")
        for prop in self.db.paramdef.properties():
            units = self.db.paramdef.units(prop)
            self.ok(prop, units)

    @test
    def api_paramdef_vartypes(self):
        self.msg("Checking list of vartypes")
        vartypes = self.db.paramdef.vartypes()
        self.ok(vartypes)

    @test
    def test_vartype(self):
        self.msg("Checking vartypes")
        for i in self.db.paramdef.vartypes():
            pd = self.db.paramdef.new(vartype=i, desc_short='Test %s'%i)
            self.db.paramdef.put(pd)
            self.ok(i)

        self.msg("Checking vartype is immutable")
        try:
            pd = self.db.paramdef.get('root')
            pd.vartype = "string"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)

        self.msg("Checking invalid vartype")
        try:
            pd = self.db.paramdef.new(vartype="invalidvartype", desc_short='Test invalid vartype')
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
    
    @test
    def test_property(self):
        self.msg("Checking properties")
        for prop in self.db.paramdef.properties():
            pd = self.db.paramdef.new(vartype='float', desc_short='Test property %s'%prop, property=prop)
            pd = self.db.paramdef.put(pd)
            assert pd.property == prop
            self.ok(prop)
            
        self.msg("Checking immutable property")
        try:
            pd = self.db.paramdef.get('root')
            pd.property = "length"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)

        self.msg("Checking invalid property")
        try:
            self.db.paramdef.new(vartype='float', desc_short='Test invalid property')
            pd.vartype = "invalidproperty"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
            
        self.msg("Checking property only for float")
        try:
            self.db.paramdef.new(vartype='string', desc_short='Test invalid property')
            pd.vartype = "length"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
    
    @test
    def test_units(self):
        import emen2.db.properties
        for prop in self.db.paramdef.properties():
            self.msg('Checking property / units:', prop)
            units = self.db.paramdef.units(prop)
            for defaultunits in units:
                pd = self.db.paramdef.new(vartype='float', property=prop, defaultunits=defaultunits, desc_short='Test property %s units %s'%(prop, units))
                pd = self.db.paramdef.put(pd)
                assert pd.vartype == 'float'                
                # assert pd.defaultunits == defaultunits
            self.ok(units)

            propcls = emen2.db.properties.Property.get_property(prop)
            for defaultunits in units:
                try:
                    value = propcls.convert(1.0, defaultunits, propcls.defaultunits)
                    self.ok("1.0 %s -> %s %s"%(defaultunits, value, propcls.defaultunits))
                except Exception, e:
                    self.fail("%s -> %s"%(defaultunits, propcls.defaultunits), e)
                    # print "--- Failed!"
                    # print e
                    # print defaultunits
                    # print propcls.defaultunits
                    # print "--------------"

        
        
    @test
    def test_desc(self):
        pass
        
    @test
    def test_choices(self):
        pass
    
    @test
    def test_iter(self):
        pass
        

######################################

class Rel(Test):
    def api_rel_pclink(self):
        pass

    def api_rel_pcunlink(self):
        pass

    def api_rel_relink(self):
        pass

    def api_rel_siblings(self):
        pass

    def api_rel_parents(self):
        pass

    def api_rel_children(self):
        pass    

    def api_rel_tree(self):
        pass

######################################

class RecordDef(Test):
    def setup(self):
        pass

    @test
    def api_recorddef_new(self):
        pass

    @test
    def api_recorddef_put(self):
        pass

    @test
    def api_recorddef_get(self):
        pass

    @test
    def api_recorddef_filter(self):
        pass

    @test
    def api_recorddef_find(self):
        pass

    @test
    def test_mainview(self):
        pass
    
    @test
    def test_views(self):
        pass
        
    @test
    def test_private(self):
        pass
        
    @test
    def test_params(self):
        pass
    
    @test
    def test_desc(self):
        pass

######################################

@register
class Record(Test):    
    def setup(self):
        root = self.db.record.new(rectype='root', inherit=['root'])
        root = self.db.record.put(root)
        self.root = root
        self.recs = []
        for i in range(10):
            rec = self.db.record.new(rectype='root', inherit=[self.root.name])
            rec = self.db.record.put(rec)
            self.recs.append(rec.name)
        assert self.root
        assert self.recs
    
    @test
    def api_record_new(self):
        # New record test
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.new(rectype='root', inherit=[self.root.name])
        assert self.root.name in rec.parents
        return rec
        
    @test
    def api_record_put(self):
        rec = self.api_record_new()
        rec = self.db.record.put(rec)
        assert rec.name
        assert rec.rectype == 'root'
        assert self.root.name in rec.parents
        return rec
        
    @test
    def api_record_get(self):
        assert self.db.record.get(self.root.name)
        try:
            self.db.record.get('fail', filt=False)
        except KeyError:
            pass

    @test
    def api_record_hide(self):
        pass
    
    @test
    def api_record_update(self):
        pass
    
    @test
    def api_record_validate(self):
        pass
    
    @test
    def api_record_adduser(self):
        pass
    
    @test
    def api_record_removeuser(self):
        pass

    @test
    def api_record_addgroup(self):
        pass
    
    @test
    def api_record_removegroup(self):
        pass
    
    @test
    def api_record_setpermissionscompat(self):
        # ugh
        pass
    
    @test
    def api_record_addcomment(self):
        pass
    
    @test
    def api_record_findcomments(self):
        pass

    @test
    def api_record_findorphans(self):
        pass

    @test
    def api_record_findbyrectype(self):
        pass
    
    @test
    def api_record_findbyvalue(self):
        pass
    
    @test
    def api_record_groupbyrectype(self):
        pass
    
    @test
    def api_record_renderchildren(self):
        pass

    @test
    def api_record_findpaths(self):
        pass
    
######################################

@register
class Binary(Test):
    @test
    def api_binary_get(self):
        pass
    
    @test
    def api_binary_new(self):
        pass
    
    @test
    def api_binary_find(self):
        pass

    @test
    def api_binary_filter(self):
        pass

    @test
    def api_binary_put(self):
        pass

    @test
    def api_binary_upload(self):
        pass
    
    @test
    def api_binary_addreference(self):
        pass
    
######################################

@register    
class Query(Test):
    @test
    def api_query(self):
        pass

    @test
    def api_table(self):
        pass    

    @test
    def api_plot(self):
        pass

######################################

@register
class Render(Test):
    @test
    def api_render(self):
        print db.render('root')    

    @test
    def api_view(self):
        print db.view('root')    
    
######################################

if __name__ == "__main__":
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument("--tmp", help="Use temporary database and run all tests.", action="store_true")
    opts.add_argument("--create", help="Run database setup before test.", action="store_true")
    opts.add_argument("--test", help="Test to run. Default is all.", action="append")
    args = opts.parse_args()
    
    dbtmp = None
    if args.tmp:
        dbtmp = tempfile.mkdtemp(suffix=".db")
        emen2.db.config.config.sethome(dbtmp)
        
    db = emen2.db.opendb(admin=True)
    t = RunTests(db=db)
    if args.tmp or args.create:
        t.runone(cls=Create)
    if args.test:
        for i in args.test:
            t.runone(i)
    else:
        t.run()
    
    if dbtmp:
        shutil.rmtree(dbtmp)
