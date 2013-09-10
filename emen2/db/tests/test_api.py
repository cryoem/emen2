#!/usr/bin/env python
import collections
import random
import string
import inspect

def randword(length):
    s = string.lowercase + string.digits
    return ''.join(random.sample(s,length))

EMAIL = '%s@sierra.example.com'%randword(10)
PASSWORD = randword(10)

import emen2.db.exceptions

######################################

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

    def setup(self):
        pass

    def run(self):
        print "\n===== Setup: %s"%self
        with self.db:
            self.setup()
        for method in self._tests():
            print "\n===== Testing: %s"%method
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
    def time_now(self):
        print self.db.time.now()

    @test
    def time_difference(self):
        print self.db.time.difference('2013-01-01')

@register
class Version(Test):
    @test
    def version(self):
        print self.db.version()

@register
class Ping(Test):
    @test
    def ping(self):
        print self.db.ping()
    
######################################

@register
class NewUser(Test):
    @test
    def newuser_new(self):
        email = '%s@yosemite.exmaple.com'%randword(10)
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        return user

    @test
    def newuser_request(self):
        user = self.db.newuser.request(self.newuser_new())
        return user

    @test
    def newuser_approve(self):
        user = self.newuser_request()
        self.db.newuser.approve(user.name)

    @test
    def newuser_reject(self):
        user = self.newuser_request()
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
    def user_get(self):
        user = self.db.user.get(self.username)
        # Check filt=False
        try:
            self.db.user.get('fail', filt=False)
        except KeyError:
            pass
        return user

    @test
    def user_put(self):
        user = self.db.user.get(self.username)
        user['name_first'] = "Test"
        self.db.user.put(user)

    @test
    def user_filter(self):
        pass

    @test
    def user_find(self):
        pass

    @test
    def user_setprivacy(self):
        self.db.user.setprivacy(self.username, 0)
        assert self.db.user.get(self.username).privacy == 0
        self.db.user.setprivacy(self.username, 1)
        assert self.db.user.get(self.username).privacy == 1
        self.db.user.setprivacy(self.username, 2)
        assert self.db.user.get(self.username).privacy == 2
        # Reset state
        self.db.user.setprivacy(self.username, 0)

    @test
    def user_disable(self):
        self.db.user.disable(self.username)
        assert self.db.user.get(self.username).disabled == True
        # Reset state
        self.db.user.enable(self.username)
        assert self.db.user.get(self.username).disabled == False

    @test
    def user_enable(self):
        self.db.user.enable(self.username)
        assert self.db.user.get(self.username).disabled == False

    @test
    def user_setpassword(self):
        # Change password, and make sure we can login.
        newpassword = self.password[::-1]        
        self.db.user.setpassword(self.username, newpassword, password=self.password)
        self.db.auth.login(self.username, newpassword)
        # Reset state
        self.db.user.setpassword(self.username, self.password, password=newpassword)
        self.db.auth.login(self.username, self.password)

    @test
    def user_setemail(self):
        # Change email, and make sure email index is updated for login.
        email = '%s@change.example.com'%randword(10)
        self.db.user.setemail(self.username, email, password=self.password)
        self.db.auth.login(email, self.password)
        # Reset state
        self.db.user.setemail(self.username, self.email, password=self.password)
        self.db.auth.login(self.email, self.password)

    @test
    def user_resetpassword(self):
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
    def user_expirepassword(self):
        self.db.user.expirepassword(self.username)

######################################

def group_(self):
    pass

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
    def auth_login(self):
        print self.db.auth.login(self.username, self.password)

    @test
    def auth_check_context(self):
        print self.db.auth.check.context()

    @test
    def auth_check_admin(self):
        print self.db.auth.check.admin()

    @test
    def auth_check_create(self):
        print self.db.auth.check.create()

    # @test
    # def auth_logout(self):
    #     print self.db.auth.logout()
    #     print self.db.auth.login("root", PASSWORD)

######################################

class ParamDef(Test):
    def paramdef_get(self):
        pass

    def paramdef_new(self):
        pass

    def paramdef_put(self):
        pass

    def paramdef_filter(self):
        pass

    def paramdef_find(self):
        pass

    def paramdef_properties(self):
        pass

    def paramdef_units(self):
        pass

    def paramdef_vartypes(self):
        pass

######################################

class Rel(Test):
    def rel_pclink(self):
        pass

    def rel_pcunlink(self):
        pass

    def rel_relink(self):
        pass

    def rel_siblings(self):
        pass

    def rel_parents(self):
        pass

    def rel_children(self):
        pass    

    def rel_tree(self):
        pass

######################################

class RecordDef(Test):
    def recorddef_(self):
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
    def record_get(self):
        assert self.db.record.get(self.root.name)
        try:
            self.db.record.get('fail', filt=False)
        except KeyError:
            pass

    @test
    def record_new(self):
        # New record test
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.new(rectype='root', inherit=[self.root.name])
        assert self.root.name in rec.parents
        
    def record_hide(self):
        pass
    

    def record_update(self):
        pass
    

    def record_validate(self):
        pass
    

    def record_adduser(self):
        pass
    

    def record_removeuser(self):
        pass
    

    def record_addgroup(self):
        pass
    

    def record_removegroup(self):
        pass
    

    def record_setpermissionscompat(self):
        # ugh
        pass
    

    def record_addcomment(self):
        pass
    

    def record_findcomments(self):
        pass


    def record_findorphans(self):
        pass


    def record_findbyrectype(self):
        pass
    

    def record_findbyvalue(self):
        pass
    

    def record_groupbyrectype(self):
        pass
    

    def record_renderchildren(self):
        pass


    def record_findpaths(self):
        pass
    
######################################

class Binary(Test):
    def binary_get(self):
        pass
    
    def binary_new(self):
        pass
    
    def binary_find(self):
        pass

    def binary_filter(self):
        pass

    def binary_put(self):
        pass

    def binary_upload(self):
        pass
    
    def binary_addreference(self):
        pass
    
######################################
    
class Query(Test):
    @test
    def query(self):
        pass

    @test
    def table(self):
        pass    

    @test
    def plot(self):
        pass

######################################

class Render(Test):
    @test
    def render(self):
        pass    

    @test
    def view(self):
        pass
    
######################################

if __name__ == "__main__":
    pass
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument("--create", help="Run database setup before test.", action="store_true")
    opts.add_argument("--test", help="Test to run. Default is all.", action="append")
    args = opts.parse_args()
    db = emen2.db.opendb(admin=True)
    t = RunTests(db=db)
    if args.create:
        t.runone(cls=Create)
    if args.test:
        for i in args.test:
            t.runone(i)
    else:
        t.run()
