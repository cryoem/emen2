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
import uuid
import unittest

def randword(length=10):
    s = string.lowercase + string.digits
    data = [random.sample(s, 1)[0] for i in range(length)]
    return ''.join(data)

PASSWORD = randword()
print "Using password:", PASSWORD

######################################
import emen2.db.exceptions
from emen2.db.exceptions import *


class DBTest(unittest.TestCase):
  def setUp(self):
    self.db = None

class TestTime(DBTest):
    def test_time_now(self):
        self.db.time.now()

    def api_time_difference(self):
        self.db.time.difference('2013-01-01')

class TestVersion(DBTest):
    def test_version(self):
        self.db.version()
        


class TestPing(DBTest):
    def test_ping(self):
        self.db.ping()
        

######################################


class TestNewUser(DBTest):
    
    def test_newuser_new(self):
        """Testing newuser.new()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
    
    
    def test_newuser_request(self):
        """Testing newuser.request()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        user = self.db.newuser.request(user)
    
    
    def test_newuser_approve(self):
        """Testing newuser.approve()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        user = self.db.newuser.request(user)
        self.db.newuser.approve(user.name)
        assert user.name not in self.db.newuser.filter()
        user = self.db.user.get(user.name)
        assert user.name
    
    
    def test_newuser_reject(self):
        """Testing newuser.reject()"""
        email = '%s@yosemite.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Chiura', name_last='Obata')
        user = self.db.newuser.request(user)
        self.db.newuser.reject(user.name)
        assert user.name not in self.db.newuser.filter()


class TestUser(DBTest):
    def _make(self):
        email = '%s@yosemite.exmaple.com'%randword()
        user = self.db.newuser.new(email=email, password=PASSWORD, name_first='John', name_last='Muir', name_middle=randword())
        user = self.db.newuser.request(user)
        return self.db.newuser.approve(user.name)
    
    
    def test_user_get(self):
        """Testing user.get()"""
        user = self._make()
        user = self.db.user.get(user.name)
        # Check filt=False
        try:
            self.db.user.get('fail', filt=False)
            raise ExpectException
        except KeyError:
            pass
        
    
    
    def test_user_put(self):
        """Testing user.put()"""
        user = self._make()
        user = self.db.user.put(user)
        user['name_first'] = "Test"
        user = self.db.user.put(user)
        assert user.name_first == "Test"
        
    
    
    def test_user_filter(self):
        """Testing user.filter()"""
        user = self._make()
        users = self.db.user.filter()
        assert users
        assert user.name in users
    
    
    def test_user_find(self):
        """Testing user.find()"""
        user = self._make()

        users = self.db.user.find(user.name_first)
        assert user.name in [i.name for i in users]

        users = self.db.user.find(user.name_last)
        assert user.name in [i.name for i in users]

        # Unique middle name
        users = self.db.user.find(user.name_middle)
        assert user.name in [i.name for i in users]
        assert len(users) == 1

        # Email
        users = self.db.user.find(user.email)
        assert user.name in [i.name for i in users]
    
    
    def test_user_setprivacy(self):
        """Testing user.setprivacy()"""
        # TODO: Check the result of non-admin user getting user.
        user = self._make()
        self.db.user.setprivacy(user.name, 0)
        assert self.db.user.get(user.name).privacy == 0

        self.db.user.setprivacy(user.name, 1)
        assert self.db.user.get(user.name).privacy == 1

        self.db.user.setprivacy(user.name, 2)
        assert self.db.user.get(user.name).privacy == 2
    
    
    def test_user_disable(self):
        """Testing user.disable()"""
        # TODO: Check user cannot login after disabled.
        user = self._make()
        self.db.user.disable(user.name)
        assert self.db.user.get(user.name).disabled == True

        self.db.user.enable(user.name)
        assert self.db.user.get(user.name).disabled == False
    
    
    def test_user_enable(self):
        """Testing user.enable()"""
        user = self._make()
        self.db.user.enable(user.name)
        assert self.db.user.get(user.name).disabled == False
    
    
    def test_user_setpassword(self):
        """Testing user.setpassword()"""
        # Change password, and make sure we can login.
        user = self._make()
        newpassword = PASSWORD[::-1]
        self.db.user.setpassword(user.name, newpassword, password=PASSWORD)
        ctxid = self.db.auth.login(user.name, newpassword)
        assert ctxid
    
    
    def test_user_setemail(self):
        """Testing user.setemail()"""
        # Change email, and make sure email index is updated for login.
        user = self._make()
        email = '%s@change.example.com'%randword()
        self.db.user.setemail(user.name, email, password=PASSWORD)
        self.db.auth.login(email, PASSWORD)
        user = self.db.user.get(user.name)
        assert user.email == email
    
    
    def test_user_resetpassword(self):
        """Testing user.resetpassword()"""
        user = self._make()
        try:
            self.db.user.resetpassword(user.name)
        except emen2.db.exceptions.EmailError:
            return
        # Get secret.
        user = self.db._db['user']._get(user.name, txn=self.db._txn)
        secret = user.data.get('secret')
        newpassword = PASSWORD[::-1]
        self.db.user.setpassword(user.name, password=newpassword, secret=secret)
        
    
    
    def test_user_expirepassword(self):
        """Testing user.expirepassword()"""
        user = self._make()
        self.db.user.expirepassword(user.name)
    
    
    def test_test_change_displayname(self):
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
    
    
    def test_test_secret(self):
        user = self._make()

        # First, check it works.
        user.resetpassword()
        secret = user.data['secret']
        assert user.checksecret(secret[0], secret[1], secret[2])
        
        # Check that it can't be set directly...
        user = self.db.user.put(user)
        assert not user.get('secret')
 
        # Check that it's stripped out by setContext
        self.db.user.setemail(user.name, '%s@reset.example.com'%randword())
        user = self.db.user.get(user.name)
        assert not user.get('secret')
        
        # user = self.db._db['user']._get(user.name, txn=self.db._txn)
        # print user.data
        # assert user.get('secret')

######################################


class TestGroup(DBTest):
    def _make(self):
        group = self.db.group.new(displayname="Farm Security Administration")
        group = self.db.group.put(group)
        return group
    
    
    def test_group_new(self):
        """Testing group.new()"""
        group = self.db.group.new(displayname="Tennessee Valley Authority")
    
    
    def test_group_put(self):
        """Testing group.put()"""
        group = self.db.group.new(displayname="Works Progress Administration")
        group = self.db.group.put(group)
    
    
    def test_group_filter(self):
        """Testing group.filter()"""
        group = self._make()
        groups = self.db.group.filter()
        assert group.name in groups
    
    
    def test_group_find(self):
        """Testing group.find()"""
        group = self._make()
        word = randword()
        group.displayname = "Random Group %s"%(word)
        group = self.db.group.put(group)
        for i in ['Random', 'Group', word]:
            groups = self.db.group.find(i)
            assert group.name in [i.name for i in groups]
        
    
    
    def test_test_group_members(self):
        """Testing group member editing"""
        # Add users
        group = self._make()
        users = self.db._db['user'].data.keys()
        users = list(users)
        users = random.sample(users, 4)
        for i in users:
            group.adduser(i)
        group = self.db.group.put(group)
        for i in users:
            assert i in group.members()
        
        # Remove a user
        for i in users:
            group.removeuser(i)
        group = self.db.group.put(group)
        for i in users:
            assert i not in group.members()
    
    
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
        

######################################


class TestAuth(DBTest):
    def test_setup(self):
        # Create account
        email = '%s@moonrise.exmaple.com'%randword()
        password = randword(10)
        user = self.db.newuser.new(email=email, password=password, name_first='Ansel', name_last='Adams')
        user = self.db.newuser.request(user)
        self.db.newuser.approve(user.name)
        self.email = email
        self.password = password
        self.username = user.name
    
    
    def test_auth_login(self):
        """Testing auth.login()"""
        ctxid = self.db.auth.login(self.username, self.password)
        assert ctxid
        # assert self.username == self.db.auth.check.context()[0]
        
    
    
    def test_auth_check_context(self):
        """Testing auth.check.context()"""
        user, groups = self.db.auth.check.context()
        # assert self.username == user
        # assert 'authenticated' in groups
        
    
    
    def test_auth_check_admin(self):
        """Testing auth.check.admin()"""
        admin = self.db.auth.check.admin()
        assert admin
        
    
    
    def test_auth_check_create(self):
        """Testing auth.check.create()"""
        create = self.db.auth.check.create()
        assert create
        
    
    # 
    # def test_auth_logout(self):
    #     print self.db.auth.logout()
    #     print self.db.auth.login("root", PASSWORD)

######################################


class TestParamDef(DBTest):
    def _make(self):
        pd = self.db.paramdef.new(vartype='float', desc_short='Numerical Aperture %s'%randword())
        pd = self.db.paramdef.put(pd)
        return pd
    
    
    def test_paramdef_new(self):
        """Testing paramdef.new()"""
        pd = self.db.paramdef.new(vartype='int', desc_short='Film speed')
    
    
    def test_paramdef_put(self):
        """Testing paramdef.put()"""
        pd = self.db.paramdef.new(vartype='int', desc_short='Film speed')
        pd = self.db.paramdef.put(pd)
        assert pd.name
        assert pd.vartype == 'int'
        assert pd.desc_short == 'Film speed'
    
    
    def test_paramdef_get(self):
        """Testing paramdef.get()"""
        pd = self._make()
        pd = self.db.paramdef.get(pd.name)
        try:
            pd = self.db.paramdef.get(randword(), filt=False)
            raise ExpectException
        except KeyError, e:
            pass
    
    
    def test_paramdef_filter(self):
        pd = self._make()
        pds = self.db.paramdef.filter()
        assert pd.name in pds
        
    
    
    def test_paramdef_find(self):
        pd = self._make()
        for word in pd.desc_short.split(" "):
            pds = self.db.paramdef.find(word)
            # print "Found:", pds
            assert pd.name in [i.name for i in pds]
    
    
    def test_paramdef_properties(self):
        """Testing list of properties"""
        props = self.db.paramdef.properties()
    
    
    def test_paramdef_units(self):
        """Testing list of units"""
        for prop in self.db.paramdef.properties():
            units = self.db.paramdef.units(prop)
    
    
    def test_paramdef_vartypes(self):
        """Testing list of vartypes"""
        vartypes = self.db.paramdef.vartypes()
    
    
    def test_vartype(self):
        """Testing vartypes"""
        for i in self.db.paramdef.vartypes():
            pd = self.db.paramdef.new(vartype=i, desc_short='Test %s'%i)
            self.db.paramdef.put(pd)
        
        # self.msg('Testing vartype is immutable')
        try:
            pd = self.db.paramdef.get('root')
            pd.vartype = "string"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            pass
        
        # self.msg('Testing for invalid vartypes')
        try:
            pd = self.db.paramdef.new(vartype="invalidvartype", desc_short='Test invalid vartype')
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            pass
    
    
    def test_property(self):
        """Testing properties"""
        for prop in self.db.paramdef.properties():
            p = emen2.db.properties.Property.get_property(prop)
            pd = self.db.paramdef.new(vartype='float', desc_short='Test property %s'%prop, property=prop, defaultunits=p.defaultunits)
            pd = self.db.paramdef.put(pd)
            assert pd.property == prop
        
        # self.msg('Testing property is immutable')
        try:
            pd = self.db.paramdef.get('root')
            pd.property = "length"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
          pass
          
        # self.msg('Testing for invalid properties')
        try:
            self.db.paramdef.new(vartype='float', desc_short='Test invalid property')
            pd.vartype = "invalidproperty"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            pass
        
        # self.msg('Testing that properties can only be set for float vartype')
        try:
            self.db.paramdef.new(vartype='string', desc_short='Test invalid property')
            pd.vartype = "length"
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            pass
    
    
    def test_units(self):
        """Testing units"""
        import emen2.db.properties
        def _convert(value, u1, u2):
            try:
                value = propcls.convert(1.0, u1, u2)
            except Exception, e:
                pass
                # self.warn("%s -> %s"%(u1, u2), e)
        
        for prop in self.db.paramdef.properties():
            # self.msg('Testing property / units:', prop)
            units = self.db.paramdef.units(prop)
            for defaultunits in units:
                print prop, defaultunits
                pd = self.db.paramdef.new(vartype='float', property=prop, defaultunits=defaultunits, desc_short='Test property %s units %s'%(prop, units))
                pd = self.db.paramdef.put(pd)
                assert pd.vartype == 'float'
                # assert pd.defaultunits == defaultunits
            
            propcls = emen2.db.properties.Property.get_property(prop)
            
            if propcls.defaultunits not in units:
                _convert(1, propcls.defaultunits, propcls.defaultunits)
            for u1 in units:
                for u2 in units:
                    _convert(1, u1, u2)
    
    
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
        
    
    
    def test_choices(self):
        """Testing choices"""
        choices1 = ['one', 'two']
        choices2 = ['two', 'three']
        pd = self.db.paramdef.new(vartype='string', desc_short='Test', choices=choices1)
        pd = self.db.paramdef.put(pd)
        assert pd.choices == choices1

        pd.choices = choices2
        pd = self.db.paramdef.put(pd)
        assert pd.choices == choices2
    
    
    def test_iter(self):
        """Testing iter"""
        pd = self.db.paramdef.new(vartype='string', desc_short='Test', iter=True)
        pd = self.db.paramdef.put(pd)
        assert pd.iter
        
        # self.msg('Testing iter is immutable')
        try:
            pd = self.db.paramdef.new(vartype='string', desc_short='Test', iter=True)
            pd = self.db.paramdef.put(pd)
            pd.iter = False
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            pass
        try:
            pd = self.db.paramdef.new(vartype='string', desc_short='Test', iter=False)
            pd = self.db.paramdef.put(pd)
            pd.iter = True
            self.db.paramdef.put(pd)
            raise ExpectException
        except ValidationError, e:
            pass

######################################


class TestRel(DBTest):
    
    def test_rel_pclink(self):
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
        

    
    def test_rel_pcunlink(self):
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
        
    
    
    def test_rel_relink(self):
        raise TestNotImplemented
    
    
    def test_rel_siblings(self):
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
        

    
    def test_rel_children(self):
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
        

    
    def test_rel_parents(self):
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
        
        # TODO: Test other options, such as filters and tree
    
    
    def test_rel_tree(self):
        raise TestNotImplemented

######################################


class TestRecordDef(DBTest):
    def _make(self):
        rd = self.db.recorddef.new(mainview="Test: {{creator}} @ {{creationtime}} %s"%randword(), desc_short="%s test"%randword())
        rd = self.db.recorddef.put(rd)
        return rd

    
    def test_recorddef_new(self):
        """Testing recorddef.new()"""
        rd = self.db.recorddef.new(mainview="Test: {{creator}} @ {{creationtime}}")
        
    
    
    def test_recorddef_put(self):
        """Testing recorddef.put()"""
        mainview = "Test: {{creator}} @ {{creationtime}}"
        rd = self.db.recorddef.new(mainview=mainview)
        rd = self.db.recorddef.put(rd)
        assert rd.mainview == mainview
        
    
    
    def test_recorddef_get(self):
        """Testing recorddef.get()"""
        rd = self._make()
        rd = self.db.recorddef.get(rd.name)
        # Check filt=False
        try:
            self.db.recorddef.get(randword(), filt=False)
            raise ExpectException
        except KeyError:
            pass
        
    
    
    def test_recorddef_filter(self):
        """Testing recorddef.filter()"""
        rd = self._make()
        rds = self.db.recorddef.filter()
        assert rd.name in rds
        
    
    
    def test_recorddef_find(self):
        """Testing recorddef.find()"""
        rd = self._make()
        for word in rd.desc_short.split(" "):
            rds = self.db.recorddef.find(word)
            assert rd.name in [i.name for i in rds]

    
    def test_test_mainview(self):
        rd = self._make()

        # self.msg('Testing mainview editing')
        word = randword()
        rd.mainview = 'A new mainview by {{creator}}, and here is a random word: %s'%word
        rd = self.db.recorddef.put(rd)
        

        # self.msg('Testing mainview keyword search')
        rds = self.db.recorddef.find(word)
        assert rd.name in [i.name for i in rds]
        

        # self.msg('Testing mainview is required')
        rd = self.db.recorddef.new()
        rd.mainview = None
        try:
            self.db.recorddef.put(rd)
            raise ExpectException
        except ValidationError, e:
            pass
        
    
    
    def test_test_views(self):
        """Testing recorddef views"""
        rd = self._make()
        view = "Test recname: {{name}} {{rectype}}"
        rd.views['recname'] = view
        rd = self.db.recorddef.put(rd)
        assert rd.views['recname'] == view
            
    
    def test_test_privacy(self):
        """Testing recorddef privacy status"""
        rd = self._make()
        
        rd.privacy = 0
        rd = self.db.recorddef.put(rd)
        assert rd.privacy == 0
        
        rd.privacy = 1
        rd = self.db.recorddef.put(rd)
        assert rd.privacy == 1
        
    
    def test_test_params(self):
        raise TestNotImplemented
    
    
    def test_test_desc(self):
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
        
        
        # self.msg('Testing keyword search')
        rds = self.db.recorddef.find(word)
        assert rd.name in [i.name for i in rds]
        

######################################


class TestRecord(DBTest):
    def _make(self):
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.put(rec)
        return rec
    
    
    def test_record_new(self):
        """Testing record.new()"""
        # New record test
        root = self.db.rel.root(keytype='record')
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.new(rectype='root', inherit=[root])
        
    
    
    def test_record_put(self):
        """Testing record.put()"""
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.put(rec)
        assert rec.name
        assert rec.rectype == 'root'
        
    
    
    def test_record_get(self):
        """Testing record.get()"""
        rec = self._make()
        rec = self.db.record.get(rec.name)
        try:
            self.db.record.get(randword(), filt=False)
        except KeyError:
            pass
        
    
    
    def test_record_hide(self):
        """Testing record.hide()"""
        # TODO: Fix relationship
        rec = self._make()
        self.db.record.hide(rec.name)
        rec = self.db.record.get(rec.name)
        assert rec.hidden
        for level in rec.permissions:
            assert not level
        
        
    
    def test_record_update(self):
        """Testing record.update()"""        
        rec = self._make()
        word = 'Hello!'
        self.db.record.update(rec.name, {'desc_short':word})
        rec = self.db.record.get(rec.name)
        assert rec.get('desc_short') == word
        
    
    
    def test_record_validate(self):
        """Testing record.validate()"""        
        rec = self._make()
        rec = self.db.record.validate(rec)
        try:
            rec.rectype = 'invalid-%s'%randword()
            self.db.record.validate(rec)
            raise ExpectException
        except ValidationError, e:
            pass
        
    
    
    def test_record_adduser(self):
        """Testing record.adduser()"""        
        rec = self._make()        
        user = 'test'
        for level in ['read', 'comment', 'write', 'owner']:
            rec = self.db.record.adduser(rec.name, 'test', level=level)
            assert user in rec['permissions'][level]
            assert user in rec.members()
        
    
    
    def test_record_removeuser(self):
        """Testing record.removeuser()"""        
        rec = self._make()
        for level in ['read', 'comment', 'write', 'owner']:
            user = 'test%s'%level
            rec = self.db.record.adduser(rec.name, user, level=level)
            assert user in rec.members()
        for user in rec.members():
            print "\n========= checking for:", user
            rec = self.db.record.removeuser(rec.name, user)
            print "members?:", rec.members()
            assert user not in rec.members()
        
        
    
    def test_record_addgroup(self):
        """Testing record.addgroup()"""        
        rec = self._make()
        groups = ['authenticated', 'anonymous']
        for group in groups:
            rec = self.db.record.addgroup(rec.name, group)
            assert group in rec.groups.get('read', [])
        
    
    
    def test_record_removegroup(self):
        """Testing record.removegroup()"""        
        rec = self._make()
        groups = ['authenticated', 'anonymous']
        for group in groups:
            rec = self.db.record.addgroup(rec.name, group)
            assert group in rec.groups.get('read', [])
        for group in groups:
            rec = self.db.record.removegroup(rec.name, group)
            assert group not in rec.groups.get('read', [])
        
    
    
    def test_record_setpermissionscompat(self):
        """Testing record.setpermissionscompat()"""        
        # ugh
        raise TestNotImplemented
    
    
    def test_record_addcomment(self):
        """Testing record.addcomment()"""        
        rec = self._make()
        comments = ['peace', 'is', 'always', 'beautiful']
        for comment in comments:
            self.db.record.addcomment(rec.name, comment)
            c = self.db.record.findcomments(rec.name)
            assert comment in [i.get('value') for i in c]
        
        
    
    def test_record_findcomments(self):
        """Testing record.findcomments()"""        
        rec = self._make()
        comments = ['large', 'contain', 'multitudes']
        for comment in comments:
            crec = self._make()
            crec = self.db.record.put(crec)
            self.db.record.addcomment(crec.name, comment)
            self.db.rel.pclink(rec.name, crec.name)
        children = self.db.rel.children(rec.name)

        found = self.db.record.findcomments(children)
        for comment in comments:
            assert comment in [i.get('value') for i in found]
        
    
    
    def test_record_gethistory(self):
        """Testing record.gethistory()"""
        rec = self._make()
        for i in ['e', 'i', 'o']:
            rec['desc_short'] = i
            rec = self.db.record.put(rec)
        h = self.db.record.gethistory(rec.name)
        for history in ['e', 'i', None]:
            assert history in [i.get('value') for i in h]
        
        
    
    def test_record_findorphans(self):
        """Testing record.findorphans()"""        
        raise TestNotImplemented
    
    
    def test_record_findbyrectype(self):
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
            # print "found:", found
            assert not (v ^ found)
        
        
    
    def test_record_findbyvalue(self):
        """Testing record.findbyvalue()"""        
        raise TestNotImplemented
    
    
    def test_record_groupbyrectype(self):
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
        
        
    
    def test_record_findpaths(self):
        """Testing record.findpaths()"""        
        raise TestNotImplemented

######################################


class TestBinary(DBTest):
    def _make(self):
        bdo = self.db.binary.upload({'filename':'hello.txt', 'filedata':'Hello, world!'})
        return bdo
    
    
    def test_binary_get(self):
        """Testing binary.get()"""
        bdo = self._make()
        bdo = self.db.binary.get(bdo.name)
        try:
            self.db.binary.get(randword(), filt=False)
        except KeyError:
            pass
        
    
    
    def test_binary_put(self):
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
        
        
    
    def test_binary_new(self):
        """Testing binary.new()"""        
        bdo = self.db.binary.new(filename='test.txt')
        # try:
        #     bdo = self.db.binary.new()
        #     raise ExpectException
        # except ValidationError, e:
        #     pass
        
    
    
    def test_binary_find(self):
        """Testing binary.find()"""
        bdo = self._make()
        word = "%s.txt"%(randword())
        bdo.filename = word
        bdo = self.db.binary.put(bdo)

        found = self.db.binary.find(word)
        assert bdo.name in [i.name for i in found]

        found = self.db.binary.find(bdo.md5)
        assert bdo.name in [i.name for i in found]
    
    
    def test_binary_filter(self):
        """Testing binary.filter()"""
        bdo = self._make()
        found = self.db.binary.filter()
        assert bdo.name in found
        
    
    
    def test_binary_upload(self):
        """Testing binary.upload()"""
        filename = "%s.txt"%randword(16)
        filesize = 512
        filedata = randword(filesize)
        filedata_md5 = hashlib.md5(filedata).hexdigest()
        bdo = self.db.binary.upload(dict(filename=filename, filedata=filedata))
        assert bdo.filename == filename
        assert bdo.filesize == filesize
        assert bdo.md5 == filedata_md5
        
    
    
    def test_binary_addreference(self):
        """Testing binary.addreference()"""
        bdo = self._make()
        rec = self.db.record.new(rectype='root')
        rec = self.db.record.put(rec)
        self.db.binary.addreference(rec.name, 'file_binary', bdo.name)
        rec = self.db.record.get(rec.name)
        assert rec.get('file_binary', [])
        assert bdo.name in rec.get('file_binary',[])
        

    
    def test_binary_getdata(self):
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
        

######################################


class TestRelFind(DBTest):
    
    def test_rel_find(self):
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

        found = self.db.rel.find(rec.name, 'recorddef')
        expect = set([rd.name])
        assert not found ^ expect

        found = self.db.rel.find([rec.name, rec2.name], 'recorddef')
        expect = set([rd.name, 'root'])
        assert not found ^ expect

        found = self.db.rel.find(rec2.name, 'user')
        expect = set(['root'])
        assert not found ^ expect

        found = self.db.rel.find([rec.name, rec2.name], 'user')
        expect = set(['root', user.name, user_iter.name])
        assert not found ^ expect

        found = self.db.rel.find(rec.name, 'link')
        expect = set([rec2.name])
        assert not found ^ expect

        found = self.db.rel.find(rec2.name, 'link')
        expect = set([rec.name])
        assert not found ^ expect

        # found = self.db.rel.find(rec.name, vartype='paramdef', vartype='user')
        # expect = set(['creator', 'modifyuser', pd.name, pd_iter.name])
        # assert not found ^ expect
        # 
        # found = self.db.rel.find(rec.name, 'paramdef', vartype='datetime')
        # expect = set(['creationtime', 'modifytime'])
        # assert not found ^ expect
        # 
        # found = self.db.rel.find(rec.name, 'user', name_first='Edmund')
        # expect = set([user.name])
        # assert not found ^ expect
        # 
        # TODO
        # found = self.db.rel.find(rec.name, 'binary')
        # expect = set()
        # assert not found ^ expect
            

class TestMacro(DBTest):
    
    def test_macro(self):
        raise TestNotImplemented

######################################


class TestQuery(DBTest):
    # The individual index operators are checked in another test.
    
    # Check plotting, sorting.
    
    def test_plot_string(self):
        pd = self.db.paramdef.new(vartype='string')
        pd = self.db.paramdef.put(pd)
        recs = []
        for i in range(100):
            rec = self.db.record.new(rectype='root')
            rec[pd.name] = randword()
            rec = self.db.record.put(rec)
            recs.append(rec)

        expect = [i.name for i in sorted(recs, key=lambda x:x.get(pd.name))]
        q = self.db.plot(c=[[pd.name, 'any']], sortkey=pd.name)        
        for i,j in zip(expect, q['names']):
            assert i,j
        
        # Just check reverse in this test. Assume it'll work elsewhere.
        expect = [i.name for i in sorted(recs, key=lambda x:x.get(pd.name), reverse=True)]
        q = self.db.plot(c=[[pd.name, 'any']], sortkey=pd.name, reverse=True)        
        for i,j in zip(expect, q['names']):
            assert i,j

    
    def test_plot_int(self):
        pd = self.db.paramdef.new(vartype='int')
        pd = self.db.paramdef.put(pd)
        recs = []
        for i in range(100):
            rec = self.db.record.new(rectype='root')
            rec[pd.name] = int(random.random()*1000.0)
            rec = self.db.record.put(rec)
            recs.append(rec)

        expect = [i.name for i in sorted(recs, key=lambda x:x.get(pd.name))]
        q = self.db.plot(c=[[pd.name, 'any']], sortkey=pd.name)        
        for i,j in zip(expect, q['names']):
            assert i,j
        
    
    def test_plot_float(self):
        pd = self.db.paramdef.new(vartype='float')
        pd = self.db.paramdef.put(pd)
        recs = []
        for i in range(100):
            rec = self.db.record.new(rectype='root')
            rec[pd.name] = random.random()
            rec = self.db.record.put(rec)
            recs.append(rec)

        expect = [i.name for i in sorted(recs, key=lambda x:x.get(pd.name))]
        q = self.db.plot(c=[[pd.name, 'any']], sortkey=pd.name)        
        for i,j in zip(expect, q['names']):
            assert i,j
        
    
    def test_plot_macro(self):
        pd = self.db.paramdef.new(vartype='string')
        pd = self.db.paramdef.put(pd)

        rd = self.db.recorddef.new()
        rd.mainview = 'test %s'%pd.name
        rd.views['recname'] = 'test {{%s}}'%pd.name
        rd = self.db.recorddef.put(rd)

        recs = []
        for i in range(100):
            rec = self.db.record.new(rectype=rd.name)
            rec[pd.name] = randword()
            rec = self.db.record.put(rec)
            recs.append(rec)

        expect = [i.name for i in sorted(recs, key=lambda x:x.get(pd.name))]
        q = self.db.plot(c=[[pd.name, 'any'], ['recname()']], sortkey='recname()')        
        recs = sorted(recs, key=lambda x:x.get(pd.name))
        for rec,i in zip(recs, q['recs']):
            assert i.get('recname()') == 'test %s'%(rec.get(pd.name))
            
    
    def test_table(self):
        rd = self.db.recorddef.new()
        rd.mainview = 'test {{desc_short}}'
        rd.views['recname'] = 'test {{desc_short}}'
        rd.views['tabularview'] = '{{desc_short}} {{rectype}} {{creator}} {{creationtime}}'
        rd = self.db.recorddef.put(rd)
        recs = []
        for i in range(100):
            rec = self.db.record.new(rectype=rd.name)
            rec['desc_short'] = randword()
            rec = self.db.record.put(rec)
            recs.append(rec)
        
        q = self.db.table(c=[['rectype','is',rd.name]], sortkey='desc_short')
        recs = sorted(recs, key=lambda x:x.get('desc_short'))
        for rec,i in zip(recs, q['names']):
            assert i == rec.name
            assert q['rendered'][i].get('desc_short') == rec.get('desc_short')

        q = self.db.table(c=[['rectype','is',rd.name]], sortkey='desc_short', count=10)
        recs2 = sorted(recs, key=lambda x:x.get('desc_short'))[:10]
        for rec,i in zip(recs, q['names']):
            assert i == rec.name
            assert q['rendered'][i].get('desc_short') == rec.get('desc_short')

        q = self.db.table(c=[['rectype','is',rd.name]], sortkey='desc_short', count=10, pos=10)
        recs2 = sorted(recs, key=lambda x:x.get('desc_short'))[10:20]
        for rec,i in zip(recs2, q['names']):
            assert i == rec.name
            assert q['rendered'][i].get('desc_short') == rec.get('desc_short')
    
    
    def test_query(self):
        raise TestNotImplemented

######################################


class TestRender(DBTest):
    
    def test_render(self):
        rec = self.db.record.new(rectype='root')
        rec['desc_short'] = 'Test'
        rec = self.db.record.put(rec)
        print self.db.render(rec.name)
    
    
    def test_view(self):
        rd = self.db.recorddef.new()
        rd['desc_short'] = 'Test'
        rd['mainview'] = 'mainview {{desc_short}}'
        rd['views']['recname'] = 'recname {{desc_short}}'
        rd = self.db.recorddef.put(rd)
        rec = self.db.record.new(rectype=rd.name)
        rec['desc_short'] = 'Test'
        rec = self.db.record.put(rec)        

        view = self.db.view(rec.name)
        assert view == 'recname Test'

        view = self.db.view(rec.name, viewname='mainview')
        assert view == 'mainview Test'

        view = self.db.view(rec.name, view='custom {{desc_short}}')
        assert view == 'custom Test'

    
    def test_view_edit(self):
        rd = self.db.recorddef.new()
        rd['desc_short'] = 'Test'
        rd['mainview'] = 'mainview {{desc_short}}'
        rd['views']['recname'] = 'recname {{desc_short}}'
        rd = self.db.recorddef.put(rd)
        rec = self.db.record.new(rectype=rd.name)
        rec['desc_short'] = 'Test'
        rec = self.db.record.put(rec)        
        print "edit?"
        print self.db.view(rec.name, viewname='mainview', options={'output':'form', 'markdown':True})
            
######################################
        
# 
# class TestDebugMisc(DBTest): 
#           
#     def test_check_inherit(self):
#         rec1 = self.db.record.new(rectype='root')
#         rec1 = self.db.record.put(rec1)
#         rec2 = self.db.record.new(rectype='root', inherit=[rec1.name])
#         rec2.parents = [rec1.name]
#         rec2 = self.db.record.put(rec2)
# 
#         parents = self.db.rel.parents(rec1.name)
#         children = self.db.rel.children(rec1.name)
#         print "rec1:", rec1, parents, children
#         assert not parents
#         assert rec2.name in children
# 
#         parents = self.db.rel.parents(rec2.name)
#         children = self.db.rel.children(rec2.name)
#         print "rec2:", rec2, parents, children
#         assert rec1.name in parents
#         assert not children
#         
        

class TestDebugDeadlock(DBTest):
    
    def test_debugdeadlock1(self):
        rec = self.db.paramdef.put(dict(vartype="string", desc_short=randword()))

    
    def test_debugdeadlock2(self):
        keys = self.db._db['paramdef'].data.keys(self.db._txn)
        keys = list(keys)
        print "keys:", len(keys)


class TestDebugIndex(DBTest):
    """Verify the secondary indexes and search are working."""
    def check(self, found, expect):
        for i,j in zip(sorted(found), sorted(expect)):
            # print i, "==", j
            assert i == j

    def check_ops(self, param, recs):
        values = sorted(recs.keys())
        spotcheck = [
            min(values), 
            max(values), 
            values[1], 
            values[-2], 
            values[int(len(values)*0.25)], 
            values[int(len(values)*0.5)], 
            values[int(len(values)*0.75)]
            ]
        spotcheck = sorted(spotcheck)
        
        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='>', txn=self.db._txn)
            expect = [i for i in values if i > spot]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='>=', txn=self.db._txn)
            expect = [i for i in values if i >= spot]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='<', txn=self.db._txn)
            expect = [i for i in values if i < spot]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='<=', txn=self.db._txn)
            expect = [i for i in values if i <= spot]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='==', txn=self.db._txn)
            expect = [i for i in values if i == spot]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='!=', txn=self.db._txn)
            expect = [i for i in values if i != spot]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot1, spot2 in zip(spotcheck[:-1], spotcheck[1:]):
            r = self.db._db['record'].find(param=param, key=spot1, maxkey=spot2, op='range', txn=self.db._txn)
            expect = [i for i in values if spot1 <= i <= spot2]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)

        for spot in spotcheck:
            r = self.db._db['record'].find(param=param, key=spot, op='any', txn=self.db._txn)
            expect = [i for i in values]
            found = [i[param] for i in self.db.record.get(r)]
            self.check(found, expect)
          
    
    def test_debugindex1(self):
        pd = self.db.paramdef.new(vartype="string", desc_short=randword())
        pd = self.db.paramdef.put(pd)
        for i in range(10):
            pd['desc_short'] = randword()
            pd = self.db.paramdef.put(pd)
    
    
    def test_debugindex_int(self):
        pd = self.db.paramdef.new(vartype='int', desc_short=randword())
        pd = self.db.paramdef.put(pd)
        print "pd?", pd, pd.__dict__
        recs = {}
        for i in range(-100, 100):
            rec = self.db.record.new(rectype='root')
            rec[pd.name] = i
            rec = self.db.record.put(rec)
            recs[i] = rec
        self.check_ops(pd.name, recs)

    
    def test_debugindex_float(self):
        pd = self.db.paramdef.new(vartype='float', desc_short=randword())
        pd = self.db.paramdef.put(pd)
        recs = {}
        for i in range(-100, 100):
            i = i * 0.25
            rec = self.db.record.new(rectype='root')
            rec[pd.name] = i
            rec = self.db.record.put(rec)
            recs[i] = rec
        self.check_ops(pd.name, recs)

    
    def test_debugindex_string(self):
        pd = self.db.paramdef.new(vartype='string', desc_short=randword())
        pd = self.db.paramdef.put(pd)
        recs = {}
        for i in range(200):
            i = randword()
            rec = self.db.record.new(rectype='root')
            rec[pd.name] = i
            rec = self.db.record.put(rec)
            recs[i] = rec

        self.check_ops(pd.name, recs)
            
        import string
        for spot in string.lowercase:
            r = self.db._db['record'].find(param=pd.name, key=spot, op='starts', txn=self.db._txn)
            expect = [i for i in recs.keys() if i.startswith(spot)]
            found = [i[pd.name] for i in self.db.record.get(r)]
            self.check(found, expect)
            
######################################

def main():
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument("--tmp", help="Use temporary database and run all tests.", action="store_true")
    opts.add_argument("--create", help="Run database setup before test.", action="store_true")
    opts.add_argument("--test", help="Test to run. Default is all.", action="append")
    opts.add_argument("--fastpw", help="Use MD5 password hashing to run test faster.", action="store_true")    
    opts.add_argument("--repeat", help="Repeat", action="store_true")
    args = opts.parse_args()
    
    alltime = 0.0
    dbtmp = None
    if args.tmp:
        dbtmp = tempfile.mkdtemp(suffix=".db")
        emen2.db.config.config.sethome(dbtmp)
    
    if args.fastpw:
        emen2.db.config.set('security.password_algorithm', 'MD5')
    
    db = emen2.db.opendb(admin=True)
    
    test = RunTests(db=db)
    if args.tmp or args.create:
        test.runone(cls=Create)
    iteration = 0
    while True:
        t = time.time()
        
        if args.test:
            for i in args.test:
                test.runone(i)
        else:
            test.run()
        
        t = time.time() - t
        alltime += t
        iteration += 1
        if args.repeat:
            print "======= ITERATION: %s in %0.2f ms / avg %0.2f =========="%(iteration, t*1000.0, (alltime/iteration)*1000.0)
        else:
            break
    
    test.printstats()
    
    if dbtmp:
        shutil.rmtree(dbtmp)
            
if __name__ == "__main__":
    main()