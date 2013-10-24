#!/usr/bin/env python
import collections
import random
import string
import inspect
import tempfile
import shutil
import time
import traceback
import hashlib

def randword(length=10):
    s = string.lowercase + string.digits
    data = [random.sample(s, 1)[0] for i in range(length)]
    return ''.join(data)

PASSWORD = randword()

######################################
from emen2.db.exceptions import *
class ExpectException(Exception):
    pass

class TestNotImplemented(Exception):
    pass

class RunTests(object):
    __tests = collections.OrderedDict()
    __counter = 1
    def __init__(self, db=None):
        self.db = db
        self._tests = []
        self._test_ok = []
        self._test_fail = []
        self._test_notimplemented = []
    
    @classmethod
    def test(cls, f):
        f.counter = cls.__counter
        cls.__counter += 1
        return f
    
    @classmethod
    def register(cls, c):
        cls.__tests[c.__name__] = c
    
    def printstats(self):
        print "\n====== Test Statistics ======"
        print "Test suites:", len(self._tests)
        print "Total tests:", len(self._test_ok) + len(self._test_fail) + len(self._test_notimplemented)
        print "Passed:", len(self._test_ok)
        print "Fail:", len(self._test_fail)
        print "Not Implemented:", len(self._test_notimplemented)
    
    def run(self):
        for k,c in self.__tests.items():
            self.runone(cls=c)
        
    def runone(self, k=None, cls=None):
        if k:
            cls = self.__tests[k]

        self._tests.append(cls)
        test = cls(db=self.db)
        test.run()
        self._test_ok += test._test_ok
        self._test_fail += test._test_fail
        self._test_notimplemented += test._test_notimplemented

        # cls(db=self.db).run()
    
    def coverage(self):
        for k,c in self.__tests.items():
            print c(db=self.db)._tests()


register = RunTests.register
test = RunTests.test

class Test(object):
    children = []
    def __init__(self, db=None):
        self.db = db
        self._test_ok = []
        self._test_fail = []
        self._test_notimplemented = []
    
    def _tests(self):
        methods = [f for k,f in inspect.getmembers(self, predicate=inspect.ismethod) if getattr(f, 'counter', None)]
        methods = sorted(methods, key=lambda f:getattr(f, 'counter', None))
        return methods
    
    def header(self, *msg):
        print "\n====== "+" ".join(map(unicode, msg)) + " ======"
    
    def msg(self, *msg, **kwargs):
        if 'newline' not in kwargs:
            kwargs['newline'] = False
        if kwargs.get('newline'):
            print
        print "\t"+" ".join(map(unicode, msg))
    
    def ok(self, *msg):
        self.msg("ok:", *msg, newline=False)

    def warn(self, *msg):
        self.msg("warning:", *msg, newline=False)
    
    def fail(self, *msg):
        self.msg("FAILED:", *msg, newline=False)

    def notimplemented(self, *msg):
        self.msg("not implemented:", *msg, newline=False)
    
    def setup(self):
        pass
    
    def run(self):
        self.header("Setup:", self)
        with self.db:
            self.setup()
        for method in self._tests():
            msg = "%s: %s"%(self.__class__.__name__, method.__doc__ or method.func_name)
            self.header(msg)
            with self.db:
                try:
                    method()
                    self._test_ok.append(method)
                except TestNotImplemented, e:
                    self.notimplemented(e)
                    self._test_notimplemented.append(method)
                except Exception, e:
                    self.fail(e)
                    traceback.print_exc(e)
                    self._test_fail.append(method)
        for c in self.children:
            t = c(db=self.db)
            t.run()

######################################

class Create(Test):
    def run(self):
        emen2.db.database.setup(db=self.db, rootpw=PASSWORD)

@register
class Time(Test):
    @test
    def api_time_now(self):
        self.db.time.now()
        self.ok()
    
    @test
    def api_time_difference(self):
        self.db.time.difference('2013-01-01')
        self.ok()

@register
class Version(Test):
    @test
    def api_version(self):
        self.db.version()
        self.ok()

@register
class Ping(Test):
    @test
    def api_ping(self):
        self.db.ping()
        self.ok()

######################################
        
# @register
# class DebugDeadlock(Test):
#     @test
#     def debugdeadlock1(self):
#         rec = self.db.paramdef.put(dict(vartype="string", desc_short=randword()))
# 
#     @test
#     def debugdeadlock2(self):
#         keys = self.db._db.dbenv['paramdef'].bdb.keys(self.db._txn)
#         print "keys:", len(keys)

# @register
# class DebugIndex(Test):
#     @test
#     def debugindex(self):
#         pd = self.db.paramdef.new(vartype="string", desc_short=randword())
#         pd = self.db.paramdef.put(pd)
#         for i in range(10):
#             pd['desc_short'] = randword()
#             pd = self.db.paramdef.put(pd)
#         self.ok(pd.name)
        
######################################

@register
class NewUser(Test):
    @test
    def api_newuser_new(self):
        """Testing newuser.new()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        self.ok(user)
    
    @test
    def api_newuser_request(self):
        """Testing newuser.request()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        user = self.db.newuser.request(user)
        self.ok(user)
    
    @test
    def api_newuser_approve(self):
        """Testing newuser.approve()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        user = self.db.newuser.request(user)
        self.db.newuser.approve(user.name)
        assert user.name not in self.db.newuser.filter()
        user = self.db.user.get(user.name)
        assert user.name
        self.ok(user)
    
    @test
    def api_newuser_reject(self):
        """Testing newuser.reject()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        user = self.db.newuser.request(user)
        self.db.newuser.reject(user.name)
        assert user.name not in self.db.newuser.filter()
        self.ok(user)

@register
class User(Test):
    def _make(self):
        email = '%s@yosemite.exmaple.com'%randword()
        user = self.db.newuser.new(email=email, password=PASSWORD, name_first='John', name_last='Muir', name_middle=randword())
        user = self.db.newuser.request(user)
        return self.db.newuser.approve(user.name)
    
    @test
    def api_user_get(self):
        """Testing user.get()"""
        user = self._make()
        user = self.db.user.get(user.name)
        # Check filt=False
        try:
            self.db.user.get('fail', filt=False)
            raise ExpectException
        except KeyError:
            pass
        self.ok()
    
    @test
    def api_user_put(self):
        """Testing user.put()"""
        user = self._make()
        user = self.db.user.put(user)
        user['name_first'] = "Test"
        user = self.db.user.put(user)
        assert user.name_first == "Test"
        self.ok()
    
    @test
    def api_user_filter(self):
        """Testing user.filter()"""
        user = self._make()
        users = self.db.user.filter()
        assert users
        assert user.name in users
        self.ok(len(users))
    
    @test
    def api_user_find(self):
        """Testing user.find()"""
        user = self._make()

        users = self.db.user.find(user.name_first)
        assert user.name in [i.name for i in users]
        self.ok(user.name_first)

        users = self.db.user.find(user.name_last)
        assert user.name in [i.name for i in users]
        self.ok(user.name_last)

        # Unique middle name
        users = self.db.user.find(user.name_middle)
        assert user.name in [i.name for i in users]
        assert len(users) == 1
        self.ok(user.name_middle)

        # Email
        users = self.db.user.find(user.email)
        assert user.name in [i.name for i in users]
        self.ok(user.email)
    
    @test
    def api_user_setprivacy(self):
        """Testing user.setprivacy()"""
        # TODO: Check the result of non-admin user getting user.
        user = self._make()
        self.db.user.setprivacy(user.name, 0)
        assert self.db.user.get(user.name).privacy == 0
        self.ok(0)

        self.db.user.setprivacy(user.name, 1)
        assert self.db.user.get(user.name).privacy == 1
        self.ok(1)

        self.db.user.setprivacy(user.name, 2)
        assert self.db.user.get(user.name).privacy == 2
        self.ok(2)
    
    @test
    def api_user_disable(self):
        """Testing user.disable()"""
        # TODO: Check user cannot login after disabled.
        user = self._make()
        self.db.user.disable(user.name)
        assert self.db.user.get(user.name).disabled == True
        self.ok(True)

        self.db.user.enable(user.name)
        assert self.db.user.get(user.name).disabled == False
        self.ok(False)
    
    @test
    def api_user_enable(self):
        """Testing user.enable()"""
        user = self._make()
        self.db.user.enable(user.name)
        assert self.db.user.get(user.name).disabled == False
        self.ok(False)
    
    @test
    def api_user_setpassword(self):
        """Testing user.setpassword()"""
        # Change password, and make sure we can login.
        user = self._make()
        newpassword = PASSWORD[::-1]
        self.db.user.setpassword(user.name, newpassword, password=PASSWORD)
        ctxid = self.db.auth.login(user.name, newpassword)
        assert ctxid
        self.ok(ctxid)
    
    @test
    def api_user_setemail(self):
        """Testing user.setemail()"""
        # Change email, and make sure email index is updated for login.
        user = self._make()
        email = '%s@change.example.com'%randword()
        self.db.user.setemail(user.name, email, password=PASSWORD)
        self.db.auth.login(email, PASSWORD)
        user = self.db.user.get(user.name)
        assert user.email == email
        self.ok(email)
    
    @test
    def api_user_resetpassword(self):
        """Testing user.resetpassword()"""
        user = self._make()
        try:
            self.db.user.resetpassword(user.name)
        except emen2.db.exceptions.EmailError:
            return
        # Get secret.
        user = self.db._db.dbenv['user']._get_data(user.name, txn=self.db._txn)
        secret = user.data.get('secret')
        newpassword = PASSWORD[::-1]
        self.db.user.setpassword(user.name, password=newpassword, secret=secret)
        self.ok()
    
    @test
    def api_user_expirepassword(self):
        """Testing user.expirepassword()"""
        user = self._make()
        self.db.user.expirepassword(user.name)
    
    @test
    def test_change_displayname(self):
        """Testing change displayname"""
        user = self._make()
        user = self.db.user.get(user.name)
        user.name_first = "Russell"
        user.name_last = "Lee"
        self.db.user.put(user)
        user = self.db.user.get(user.name)
        expectedname = "%s %s %s"%(user.name_first, user.name_middle, user.name_last)
        assert user.displayname == expectedname
        users = self.db.user.find("Russell")
        assert user.name in [i.name for i in users]
    
    @test
    def test_secret(self):
        user = self._make()

        # First, check it works.
        user.resetpassword()
        secret = user.data['secret']
        assert user.checksecret(secret[0], secret[1], secret[2])
        self.ok("checksecret")
        
        # Check that it can't be set directly...
        user = self.db.user.put(user)
        assert not user.get('secret')
        self.ok("prevents direct edit")
 
        # Check that it's stripped out by setContext
        self.db.user.setemail(user.name, '%s@reset.example.com'%randword())
        user = self.db.user.get(user.name)
        assert not user.get('secret')
        self.ok("prevents direct read")
        
        # user = self.db._db.dbenv['user']._get_data(user.name, txn=self.db._txn)
        # print user.data
        # assert user.get('secret')
        # self.ok("stored correctly")

######################################

@register
class Group(Test):
    def _make(self):
        group = self.db.group.new(displayname="Farm Security Administration")
        group = self.db.group.put(group)
        return group
    
    @test
    def api_group_new(self):
        """Testing group.new()"""
        group = self.db.group.new(displayname="Tennessee Valley Authority")
        self.ok(group)
    
    @test
    def api_group_put(self):
        """Testing group.put()"""
        group = self.db.group.new(displayname="Works Progress Administration")
        group = self.db.group.put(group)
        self.ok(group)
    
    @test
    def api_group_filter(self):
        """Testing group.filter()"""
        group = self._make()
        groups = self.db.group.filter()
        assert group.name in groups
        self.ok(len(groups))
    
    @test
    def api_group_find(self):
        """Testing group.find()"""
        group = self._make()
        word = randword()
        group.displayname = "Random Group %s"%(word)
        group = self.db.group.put(group)
        for i in ['Random', 'Group', word]:
            groups = self.db.group.find(i)
            assert group.name in [i.name for i in groups]
        self.ok()
    
    @test
    def test_group_members(self):
        """Testing group member editing"""
        # Add users
        group = self._make()
        users = self.db._db.dbenv['user'].bdb.keys() # self.db.group.filter()
        users = random.sample(users, 4)
        for i in users:
            group.adduser(i)
        group = self.db.group.put(group)
        for i in users:
            assert i in group.members()
        self.ok("add")
        
        # Remove a user
        for i in users:
            group.removeuser(i)
        group = self.db.group.put(group)
        for i in users:
            assert i not in group.members()
        self.ok("remove")
    
    @test
    def test_group_change_displayname(self):
        """Testing group displayname editing"""
        group = self._make()
        orig = group.displayname
        group.displayname = "Department of the Interior"
        self.db.group.put(group)
        groups = self.db.group.find("Interior")
        assert group.name in [i.name for i in groups]
        groups = self.db.group.find(orig.partition(" ")[0])
        assert group.name not in [i.name for i in groups]
        self.ok()

######################################

@register
class Auth(Test):
    def setup(self):
        # Create account
        self.msg("Setup...")
        email = '%s@moonrise.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Ansel', name_last='Adams')
        user = self.db.newuser.request(user)
        self.db.newuser.approve(user.name)
        self.email = email
        self.password = password
        self.username = user.name
    
    @test
    def api_auth_login(self):
        """Testing auth.login()"""
        ctxid = self.db.auth.login(self.username, self.password)
        assert ctxid
        # assert self.username == self.db.auth.check.context()[0]
        self.ok()
    
    @test
    def api_auth_check_context(self):
        """Testing auth.check.context()"""
        user, groups = self.db.auth.check.context()
        # assert self.username == user
        # assert 'authenticated' in groups
        self.ok()
    
    @test
    def api_auth_check_admin(self):
        """Testing auth.check.admin()"""
        admin = self.db.auth.check.admin()
        assert admin
        self.ok()
    
    @test
    def api_auth_check_create(self):
        """Testing auth.check.create()"""
        create = self.db.auth.check.create()
        assert create
        self.ok()
    
    # @test
    # def api_auth_logout(self):
    #     print self.db.auth.logout()
    #     print self.db.auth.login("root", PASSWORD)

######################################

@register
class ParamDef(Test):
    def _make(self):
        pd = self.db.paramdef.new(vartype='float', desc_short='Numerical Aperture %s'%randword())
        pd = self.db.paramdef.put(pd)
        return pd
    
    @test
    def api_paramdef_new(self):
        """Testing paramdef.new()"""
        pd = self.db.paramdef.new(vartype='int', desc_short='Film speed')
        self.ok(pd)
    
    @test
    def api_paramdef_put(self):
        """Testing paramdef.put()"""
        pd = self.db.paramdef.new(vartype='int', desc_short='Film speed')
        pd = self.db.paramdef.put(pd)
        assert pd.name
        assert pd.vartype == 'int'
        assert pd.desc_short == 'Film speed'
        self.ok(pd)
    
    @test
    def api_paramdef_get(self):
        """Testing paramdef.get()"""
        pd = self._make()
        pd = self.db.paramdef.get(pd.name)
        try:
            pd = self.db.paramdef.get(randword(), filt=False)
            raise ExpectException
        except KeyError, e:
            pass
        self.ok(pd)
    
    @test
    def api_paramdef_filter(self):
        pd = self._make()
        pds = self.db.paramdef.filter()
        assert pd.name in pds
        self.ok()
    
    @test
    def api_paramdef_find(self):
        pd = self._make()
        for word in pd.desc_short.split(" "):
            pds = self.db.paramdef.find(word)
            assert pd.name in [i.name for i in pds]
            self.ok(word)
    
    @test
    def api_paramdef_properties(self):
        """Testing list of properties"""
        props = self.db.paramdef.properties()
        self.ok(props)
    
    @test
    def api_paramdef_units(self):
        """Testing list of units"""
        for prop in self.db.paramdef.properties():
            units = self.db.paramdef.units(prop)
            self.ok(prop, units)
    
    @test
    def api_paramdef_vartypes(self):
        """Testing list of vartypes"""
        vartypes = self.db.paramdef.vartypes()
        self.ok(vartypes)
    
    @test
    def test_vartype(self):
        """Testing vartypes"""
        for i in self.db.paramdef.vartypes():
            pd = self.db.paramdef.new(vartype=i, desc_short='Test %s'%i)
            self.db.paramdef.put(pd)
            self.ok(i)
        
        self.msg('Testing vartype is immutable')
        try:
            pd = self.db.paramdef.get('root')
            pd.vartype = "string"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
        
        self.msg('Testing for invalid vartypes')
        try:
            pd = self.db.paramdef.new(vartype="invalidvartype", desc_short='Test invalid vartype')
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
    
    @test
    def test_property(self):
        """Testing properties"""
        for prop in self.db.paramdef.properties():
            pd = self.db.paramdef.new(vartype='float', desc_short='Test property %s'%prop, property=prop)
            pd = self.db.paramdef.put(pd)
            assert pd.property == prop
            self.ok(prop)
        
        self.msg('Testing property is immutable')
        try:
            pd = self.db.paramdef.get('root')
            pd.property = "length"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
        
        self.msg('Testing for invalid properties')
        try:
            self.db.paramdef.new(vartype='float', desc_short='Test invalid property')
            pd.vartype = "invalidproperty"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
        
        self.msg('Testing that properties can only be set for float vartype')
        try:
            self.db.paramdef.new(vartype='string', desc_short='Test invalid property')
            pd.vartype = "length"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
    
    @test
    def test_units(self):
        """Testing units"""
        import emen2.db.properties
        def _convert(value, u1, u2):
            try:
                value = propcls.convert(1.0, u1, u2)
                self.ok("1.0 %s -> %s %s"%(u1, value, u2))
            except Exception, e:
                self.warn("%s -> %s"%(u1, u2), e)
        
        for prop in self.db.paramdef.properties():
            self.msg('Testing property / units:', prop)
            units = self.db.paramdef.units(prop)
            for defaultunits in units:
                pd = self.db.paramdef.new(vartype='float', property=prop, defaultunits=defaultunits, desc_short='Test property %s units %s'%(prop, units))
                pd = self.db.paramdef.put(pd)
                assert pd.vartype == 'float'
                # assert pd.defaultunits == defaultunits
            self.ok(units)
            
            propcls = emen2.db.properties.Property.get_property(prop)
            
            if propcls.defaultunits not in units:
                _convert(1, propcls.defaultunits, propcls.defaultunits)
            for u1 in units:
                for u2 in units:
                    _convert(1, u1, u2)
    
    @test
    def test_desc(self):
        """Testing desc"""
        pd = self.db.paramdef.new(vartype='string', desc_short='Test', desc_long='Test change description')
        pd = self.db.paramdef.put(pd)
        new_short = 'Changed'
        new_long = 'Changed description'
        pd.desc_short = new_short
        pd.desc_long = new_long
        pd = self.db.paramdef.put(pd)
        assert pd.desc_short == new_short
        assert pd.desc_long == new_long
        self.ok()
    
    @test
    def test_choices(self):
        """Testing choices"""
        choices1 = ['one', 'two']
        choices2 = ['two', 'three']
        pd = self.db.paramdef.new(vartype='string', desc_short='Test', choices=choices1)
        pd = self.db.paramdef.put(pd)
        assert pd.choices == choices1
        self.ok(choices1)
        pd.choices = choices2
        pd = self.db.paramdef.put(pd)
        assert pd.choices == choices2
        self.ok(choices2)
    
    @test
    def test_iter(self):
        """Testing iter"""
        pd = self.db.paramdef.new(vartype='string', desc_short='Test', iter=True)
        pd = self.db.paramdef.put(pd)
        assert pd.iter
        
        self.msg('Testing iter is immutable')
        try:
            pd = self.db.paramdef.new(vartype='string', desc_short='Test', iter=True)
            pd = self.db.paramdef.put(pd)
            pd.iter = False
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)
        try:
            pd = self.db.paramdef.new(vartype='string', desc_short='Test', iter=False)
            pd = self.db.paramdef.put(pd)
            pd.iter = True
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            self.ok(e)

######################################

@register
class Rel(Test):
    @test
    def api_rel_pclink(self):
        """Testing rel.pclink()"""
        # Setup
        rec1 = self.db.record.new(rectype="root")
        rec1 = self.db.record.put(rec1)
        rec2 = self.db.record.new(rectype="root")
        rec2 = self.db.record.put(rec2)

        # Test
        self.db.rel.pclink(rec1.name, rec2.name)        
        children = self.db.rel.children(rec1.name)
        assert rec2.name in children        
        parents = self.db.rel.parents(rec2.name)
        assert rec1.name in parents
        self.ok()

    @test
    def api_rel_pcunlink(self):
        """Testing rel.pcunlink()"""
        # Setup
        rec1 = self.db.record.new(rectype="root")
        rec1 = self.db.record.put(rec1)
        rec2 = self.db.record.new(rectype="root")
        rec2 = self.db.record.put(rec2)
        self.db.rel.pclink(rec1.name, rec2.name)
        assert rec2.name in self.db.rel.children(rec1.name)
        assert rec1.name in self.db.rel.parents(rec2.name)

        # Test
        self.db.rel.pcunlink(rec1.name, rec2.name)
        children = self.db.rel.children(rec1.name)
        parents = self.db.rel.parents(rec1.name)
        assert not children
        assert not parents
        children = self.db.rel.children(rec2.name)
        parents = self.db.rel.parents(rec2.name)
        assert not children
        assert not parents
        self.ok()
    
    @test
    def api_rel_relink(self):
        raise TestNotImplemented
    
    @test
    def api_rel_siblings(self):
        """Testing rel.siblings()"""
        # Setup
        parent = self.db.record.put(dict(rectype='root'))
        children = set()
        for i in range(5):
            child = self.db.record.put(dict(rectype='root'))
            self.db.rel.pclink(parent.name, child.name)
            children.add(child.name)
        # Test
        for i in children:
            siblings = self.db.rel.siblings(i)
            assert children == siblings
        self.ok()

    @test
    def api_rel_children(self):
        """Testing rel.children()"""
        # Setup
        root = self.db.record.put(dict(rectype='root'))
        levels = []
        addchildren = set([root.name])
        for level in range(4):
            nextlevel = set()
            for child in addchildren:
                for count in range(4):
                    rec = self.db.record.put(dict(rectype='root'))
                    self.db.rel.pclink(child, rec.name)
                    nextlevel.add(rec.name)
            levels.append(nextlevel)
            addchildren = nextlevel
        allchildren = set()
        for i in levels:
            allchildren |= i
        # Test
        c_1 = self.db.rel.children(root.name, recurse=1)
        assert c_1 == levels[0]
        c_2 = self.db.rel.children(root.name, recurse=2)
        assert c_2 == (levels[0] | levels[1])
        c_3 = self.db.rel.children(root.name, recurse=3)
        assert c_3 == (levels[0] | levels[1] | levels[2])
        c_all = self.db.rel.children(root.name, recurse=-1)
        assert c_all == allchildren
        # TODO: Test other options, such as filters and tree        
        self.ok()

    @test
    def api_rel_parents(self):
        """Testing rel.parents()"""
        # Setup
        root = self.db.record.put(dict(rectype='root'))
        levels = []
        addchildren = set([root.name])
        for level in range(4):
            nextlevel = set()
            for child in addchildren:
                for count in range(4):
                    rec = self.db.record.put(dict(rectype='root'))
                    self.db.rel.pclink(child, rec.name)
                    nextlevel.add(rec.name)
            levels.append(nextlevel)
            addchildren = nextlevel
        allchildren = set()
        for i in levels:
            allchildren |= i        
        # Test
        allchildren.add(root.name)
        for count, level in enumerate(levels):
            child = random.sample(level, 1).pop()
            p_1 = self.db.rel.parents(child, recurse=1)
            assert len(p_1) == 1
            assert not p_1 - allchildren
            p_all = self.db.rel.parents(child, recurse=-1)
            assert len(p_all) == (count+1)
            assert not p_all - allchildren
        self.ok()
        # TODO: Test other options, such as filters and tree
    
    @test
    def api_rel_tree(self):
        raise TestNotImplemented

######################################

@register
class RecordDef(Test):
    def _make(self):
        rd = self.db.recorddef.new(mainview="Test: {{creator}} @ {{creationtime}} %s"%randword(), desc_short="%s test"%randword())
        rd = self.db.recorddef.put(rd)
        return rd

    @test
    def api_recorddef_new(self):
        """Testing recorddef.new()"""
        rd = self.db.recorddef.new(mainview="Test: {{creator}} @ {{creationtime}}")
        self.ok()
    
    @test
    def api_recorddef_put(self):
        """Testing recorddef.put()"""
        mainview = "Test: {{creator}} @ {{creationtime}}"
        rd = self.db.recorddef.new(mainview=mainview)
        rd = self.db.recorddef.put(rd)
        assert rd.mainview == mainview
        self.ok()
    
    @test
    def api_recorddef_get(self):
        """Testing recorddef.get()"""
        rd = self._make()
        rd = self.db.recorddef.get(rd.name)
        # Check filt=False
        try:
            self.db.recorddef.get(randword(), filt=False)
            raise ExpectException
        except KeyError:
            pass
        self.ok()
    
    @test
    def api_recorddef_filter(self):
        """Testing recorddef.filter()"""
        rd = self._make()
        rds = self.db.recorddef.filter()
        assert rd.name in rds
        self.ok()
    
    @test
    def api_recorddef_find(self):
        """Testing recorddef.find()"""
        rd = self._make()
        for word in rd.desc_short.split(" "):
            rds = self.db.recorddef.find(word)
            assert rd.name in [i.name for i in rds]
            self.ok(word)

    @test
    def test_mainview(self):
        rd = self._make()

        self.msg('Testing mainview editing')
        word = randword()
        rd.mainview = 'A new mainview by {{creator}}, and here is a random word: %s'%word
        rd = self.db.recorddef.put(rd)
        self.ok()

        self.msg('Testing mainview keyword search')
        rds = self.db.recorddef.find(word)
        assert rd.name in [i.name for i in rds]
        self.ok()

        self.msg('Testing mainview is required')
        rd = self.db.recorddef.new()
        rd.mainview = None
        try:
            self.db.recorddef.put(rd)
            raise ExpectException
        except ValidationError, e:
            pass
        self.ok()
    
    @test
    def test_views(self):
        """Testing recorddef views"""
        rd = self._make()
        view = "Test recname: {{name}} {{rectype}}"
        rd.views['recname'] = view
        rd = self.db.recorddef.put(rd)
        assert rd.views['recname'] == view
            
    @test
    def test_private(self):
        """Testing recorddef private status"""
        rd = self._make()
        
        rd.private = False
        rd = self.db.recorddef.put(rd)
        assert rd.private == False
        self.ok(False)
        
        rd.private = True
        rd = self.db.recorddef.put(rd)
        assert rd.private == True
        self.ok(True)
        
    @test
    def test_params(self):
        raise TestNotImplemented
    
    @test
    def test_desc(self):
        """Testing desc"""
        rd = self.db.recorddef.new(desc_short='Test', desc_long='Test change description', mainview='Average mainview')
        rd = self.db.recorddef.put(rd)
        word = randword()
        new_short = 'Changed'
        new_long = 'Changed description, and a random word: %s'%word
        rd.desc_short = new_short
        rd.desc_long = new_long
        rd = self.db.recorddef.put(rd)
        assert rd.desc_short == new_short
        assert rd.desc_long == new_long
        self.ok()
        
        self.msg('Testing keyword search')
        rds = self.db.recorddef.find(word)
        assert rd.name in [i.name for i in rds]
        self.ok()

######################################

@register
class Record(Test):
    def _make(self):
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.put(rec)
        return rec
    
    @test
    def api_record_new(self):
        """Testing record.new()"""
        # New record test
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.new(rectype='root', inherit=['root'])
        self.ok()
    
    @test
    def api_record_put(self):
        """Testing record.put()"""
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.put(rec)
        assert rec.name
        assert rec.rectype == 'root'
        self.ok()
    
    @test
    def api_record_get(self):
        """Testing record.get()"""
        rec = self._make()
        rec = self.db.record.get(rec.name)
        try:
            self.db.record.get(randword(), filt=False)
        except KeyError:
            pass
        self.ok()
    
    @test
    def api_record_hide(self):
        """Testing record.hide()"""
        # TODO: Fix relationship
        rec = self._make()
        self.db.record.hide(rec.name)
        rec = self.db.record.get(rec.name)
        assert rec.hidden
        for level in rec.permissions:
            assert not level
        self.ok()
        
    @test
    def api_record_update(self):
        """Testing record.update()"""        
        rec = self._make()
        word = 'Hello!'
        self.db.record.update(rec.name, {'desc_short':word})
        rec = self.db.record.get(rec.name)
        assert rec.get('desc_short') == word
        self.ok()
    
    @test
    def api_record_validate(self):
        """Testing record.validate()"""        
        rec = self._make()
        rec = self.db.record.validate(rec)
        try:
            rec.rectype = 'invalid-%s'%randword()
            self.db.record.validate(rec)
            raise ExpectException
        except ValidationError, e:
            pass
        self.ok()
    
    @test
    def api_record_adduser(self):
        """Testing record.adduser()"""        
        rec = self._make()        
        user = 'test'
        for level in range(4):
            rec = self.db.record.adduser(rec.name, 'test', level=level)
            assert user in rec['permissions'][level]
            assert user in rec.members()
        self.ok()
    
    @test
    def api_record_removeuser(self):
        """Testing record.removeuser()"""        
        rec = self._make()
        for level in range(4):
            user = 'test%s'%level
            rec = self.db.record.adduser(rec.name, user, level=level)
        for user in rec.members():
            rec = self.db.record.removeuser(rec.name, user)
            assert user not in rec.members()
        self.ok()
        
    @test
    def api_record_addgroup(self):
        """Testing record.addgroup()"""        
        rec = self._make()
        groups = ['authenticated', 'anonymous']
        for group in groups:
            rec = self.db.record.addgroup(rec.name, group)
            assert group in rec.groups
        self.ok()
    
    @test
    def api_record_removegroup(self):
        """Testing record.removegroup()"""        
        rec = self._make()
        groups = ['authenticated', 'anonymous']
        for group in groups:
            rec = self.db.record.addgroup(rec.name, group)
            assert group in rec.groups
        for group in groups:
            rec = self.db.record.removegroup(rec.name, group)
            assert group not in rec.groups
        self.ok()
    
    @test
    def api_record_setpermissionscompat(self):
        """Testing record.setpermissionscompat()"""        
        # ugh
        raise TestNotImplemented
    
    @test
    def api_record_addcomment(self):
        """Testing record.addcomment()"""        
        rec = self._make()
        comments = ['1', '2', '3']
        for comment in comments:
            rec = self.db.record.addcomment(rec.name, comment)
            assert comment in [i[2] for i in rec.comments]
        self.ok()
        
    @test
    def api_record_findcomments(self):
        """Testing record.findcomments()"""        
        rec = self._make()
        comments = ['hickory', 'dickory', 'dock']
        for comment in comments:
            crec = self._make()
            crec['comments'] = comment
            crec = self.db.record.put(crec)
            self.db.rel.pclink(rec.name, crec.name)
        children = self.db.rel.children(rec.name)
        found = self.db.record.findcomments(children)
        for comment in comments:
            assert comment in [i[3] for i in found]
        self.ok()
    
    @test
    def api_record_findorphans(self):
        """Testing record.findorphans()"""        
        raise TestNotImplemented
    
    @test
    def api_record_findbyrectype(self):
        """Testing record.findbyrectype()"""        
        # Create some rectypes
        recs = collections.defaultdict(set)
        for i in range(5):
            rd = self.db.recorddef.new(mainview="Test")
            rd = self.db.recorddef.put(rd)
            for j in range(5):
                rec = self.db.record.new(rectype=rd.name)
                rec = self.db.record.put(rec)
                recs[rd.name].add(rec.name)
        # Test
        for k,v in recs.items():
            found = self.db.record.findbyrectype(k)
            print "found:", found
            assert not (v ^ found)
        self.ok()
        
    @test
    def api_record_findbyvalue(self):
        """Testing record.findbyvalue()"""        
        raise TestNotImplemented
    
    @test
    def api_record_groupbyrectype(self):
        """Testing record.groupbyrectype()"""        
        # Create some rectypes
        recs = collections.defaultdict(set)
        allrecs = set()
        for i in range(5):
            rd = self.db.recorddef.new(mainview="Test")
            rd = self.db.recorddef.put(rd)
            for j in range(5):
                rec = self.db.record.new(rectype=rd.name)
                rec = self.db.record.put(rec)
                recs[rd.name].add(rec.name)
                allrecs.add(rec.name)
                
        grouped = self.db.record.groupbyrectype(allrecs)
        for k,v in grouped.items():            
            assert not (v ^ recs[k])
        self.ok()
        
    @test
    def api_record_findpaths(self):
        """Testing record.findpaths()"""        
        raise TestNotImplemented

######################################

@register
class Binary(Test):
    def _make(self):
        bdo = self.db.binary.upload({'filename':'hello.txt', 'filedata':'Hello, world!'})
        return bdo
    
    @test
    def api_binary_get(self):
        """Testing binary.get()"""
        bdo = self._make()
        bdo = self.db.binary.get(bdo.name)
        try:
            self.db.binary.get(randword(), filt=False)
        except KeyError:
            pass
        self.ok()
    
    @test
    def api_binary_put(self):
        """Testing binary.put()"""
        bdo = self._make()
        bdo = self.db.binary.get(bdo.name)
        # Check that we can't change certain details
        try:
            bdo.filesize = 0
            self.db.binary.put(bdo)
            raise ExpectException
        except ValidationError, e:
            pass
        self.ok()
        
    @test
    def api_binary_new(self):
        """Testing binary.new()"""        
        bdo = self.db.binary.new(filename='test.txt')
        # try:
        #     bdo = self.db.binary.new()
        #     raise ExpectException
        # except ValidationError, e:
        #     pass
        self.ok()
    
    @test
    def api_binary_find(self):
        """Testing binary.find()"""
        bdo = self._make()
        word = "%s.txt"%(randword())
        bdo.filename = word
        bdo = self.db.binary.put(bdo)

        found = self.db.binary.find(word)
        assert bdo.name in [i.name for i in found]
        self.ok(bdo.filename)

        found = self.db.binary.find(bdo.md5)
        assert bdo.name in [i.name for i in found]
        self.ok(bdo.md5)
    
    @test
    def api_binary_filter(self):
        """Testing binary.filter()"""
        bdo = self._make()
        found = self.db.binary.filter()
        assert bdo.name in found
        self.ok()
    
    @test
    def api_binary_upload(self):
        """Testing binary.upload()"""
        filename = "%s.txt"%randword(16)
        filesize = 512
        filedata = randword(filesize)
        filedata_md5 = hashlib.md5(filedata).hexdigest()
        bdo = self.db.binary.upload(dict(filename=filename, filedata=filedata))
        assert bdo.filename == filename
        assert bdo.filesize == filesize
        assert bdo.md5 == filedata_md5
        self.ok()
    
    @test
    def api_binary_addreference(self):
        """Testing binary.addreference()"""
        bdo = self._make()
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.put(rec)
        self.db.binary.addreference(rec.name, 'file_binary', bdo.name)
        rec = self.db.record.get(rec.name)
        assert rec.get('file_binary', [])
        assert bdo.name in rec.get('file_binary',[])
        self.ok()

    @test
    def binary_getdata(self):
        """Testing binary data"""
        # Have to override some transaction semantics...
        self.db.__exit__(None, None, None)
        self.db.__enter__()
        filename = "%s.txt"%randword(16)
        filesize = 512
        filedata = randword(filesize)
        filedata_md5 = hashlib.md5(filedata).hexdigest()
        bdo = self.db.binary.upload(dict(filename=filename, filedata=filedata))
        bdo = self.db.binary.get(bdo.name)
        self.db.__exit__(None, None, None)
        self.db.__enter__()
        with open(bdo.filepath) as f:
            data = f.read()
        assert data == filedata
        assert len(data) == filesize == bdo.filesize
        assert hashlib.md5(data).hexdigest() == filedata_md5 == bdo.md5
        self.ok()

######################################

@register
class RelFind(Test):
    @test
    def api_rel_find(self):
        # Create some test items.
        rd = self.db.recorddef.put(dict(mainview="Test", desc_short="Test paramdef"))
        pd = self.db.paramdef.put(dict(vartype="user", desc_short="Test user"))
        pd_iter = self.db.paramdef.put(dict(vartype="user", desc_short="Test user", iter=True))        
        user = self.db.newuser.request(dict(password=randword(), email="%s@summit.example.com"%randword(), name_first="Edmund", name_last="Hillary"))
        user = self.db.newuser.approve(user.name)
        user_iter = self.db.newuser.request(dict(password=randword(), email="%s@summit.example.com"%randword(), name_first="Tenzing", name_last="Norgay"))
        user_iter = self.db.newuser.approve(user_iter.name)

        # Create some records
        rec = self.db.record.new(rectype=rd.name)
        rec[pd.name] = user.name
        rec[pd_iter.name] = [user_iter.name]
        rec = self.db.record.put(rec)
        rec2 = self.db.record.new(rectype='root')
        rec2 = self.db.record.put(rec2)
        self.db.rel.pclink(rec.name, rec2.name)

        # Run the test
        found = self.db.rel.find(rec.name, 'paramdef')
        expect = set(rec.keys())
        assert not found ^ expect
        self.ok('paramdef', len(found))

        found = self.db.rel.find(rec.name, 'recorddef')
        expect = set([rd.name])
        assert not found ^ expect
        self.ok('recorddef', len(found))

        found = self.db.rel.find([rec.name, rec2.name], 'recorddef')
        expect = set([rd.name, 'root'])
        assert not found ^ expect
        self.ok('recorddef multiple', len(found))

        found = self.db.rel.find(rec2.name, 'user')
        expect = set(['root'])
        assert not found ^ expect
        self.ok('user', len(found))

        found = self.db.rel.find([rec.name, rec2.name], 'user')
        expect = set(['root', user.name, user_iter.name])
        assert not found ^ expect
        self.ok('user multiple', len(found))

        found = self.db.rel.find(rec.name, 'link')
        expect = set([rec2.name])
        assert not found ^ expect
        self.ok('link child', len(found))

        found = self.db.rel.find(rec2.name, 'link')
        expect = set([rec.name])
        assert not found ^ expect
        self.ok('link parent', len(found))

        found = self.db.rel.find(rec.name, 'paramdef', vartype='user')
        expect = set(['creator', 'modifyuser', pd.name, pd_iter.name])
        assert not found ^ expect
        self.ok('secondary search 1 -- paramdef[vartype=user]', len(found))

        found = self.db.rel.find(rec.name, 'paramdef', vartype='datetime')
        expect = set(['creationtime', 'modifytime'])
        assert not found ^ expect
        self.ok('secondary search 2 -- paramdef[vartype=datetime]', len(found))

        found = self.db.rel.find(rec.name, 'user', name_first='Edmund')
        expect = set([user.name])
        assert not found ^ expect
        self.ok('secondary search 3 -- user[name_first=Edmund]', len(found))

        # TODO
        # found = self.db.rel.find(rec.name, 'binary')
        # expect = set()
        # assert not found ^ expect
        # self.ok('binary', len(found))



######################################

@register
class Query(Test):
    @test
    def api_query(self):
        raise TestNotImplemented
    
    @test
    def api_table(self):
        raise TestNotImplemented
    
    @test
    def api_plot(self):
        raise TestNotImplemented

######################################

@register
class Render(Test):
    @test
    def api_render(self):
        print db.render('root')
        raise TestNotImplemented
    
    @test
    def api_view(self):
        print db.view('root')
        raise TestNotImplemented

######################################

if __name__ == "__main__":
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument("--tmp", help="Use temporary database and run all tests.", action="store_true")
    opts.add_argument("--create", help="Run database setup before test.", action="store_true")
    opts.add_argument("--test", help="Test to run. Default is all.", action="append")
    opts.add_argument("--repeat", help="Repeat", action="store_true")
    args = opts.parse_args()
    
    dbtmp = None
    if args.tmp:
        dbtmp = tempfile.mkdtemp(suffix=".db")
        emen2.db.config.config.sethome(dbtmp)
    
    db = emen2.db.opendb(admin=True)
    t = RunTests(db=db)
    if args.tmp or args.create:
        t.runone(cls=Create)
    iteration = 0
    while True:
        if args.test:
            for i in args.test:
                t.runone(i)
        else:
            t.run()

        iteration += 1
        if not args.repeat:
            break
        else:
            print "======= ITERATION: %s =========="%iteration
    
    t.printstats()
    
    if dbtmp:
        shutil.rmtree(dbtmp)
