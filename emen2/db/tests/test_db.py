import emen2.db
from twisted.trial import unittest
import getpass

import emen2.db.database
emen2.db.database.markdown = False

def match_dicts(odict, ndict, match_keys):
    return zip(*[ (odict.get(k),ndict.get(k)) for k in match_keys])

def load_db():
    import emen2.db.load as l
    import emen2.db.config as cfg

    cfg.gg.EMEN2DBHOME='/tmp/db'

    dbo = cfg.DBOptions()
    dbo.parse_args()
    db = dbo.opendb()

    with db:
        l.setup(rootpw='rootpw', rootemail='root@example.com', db=db)

    cfg.gg.log.push_state('ERROR')

    return db

class TestDB(unittest.TestCase):
    db = load_db()

    def setUp(self):
        self.db._starttxn()
        self.rec = self.db.record.put(dict(
            name_folder='Test Name',
            rectype='folder',
            parents=set([0])
        ))

    def tearDown(self):
        self.db._aborttxn()
        assert self.db.record.get(self.rec.name) is None

    def put_helper(self, putter, getter, data, match_keys):
        data1 = putter(data)
        data2 = getter(data1['name'])

        self.assertEqual(data1, data2)
        self.assertEqual(*match_dicts(data, data1, match_keys))
        self.assertEqual(*match_dicts(data, data2, match_keys))
        return data1.name

    def test_record_put_basic_invocation(self):
        record = self.db.record.new(rectype='folder')
        name = 'The Record Name'
        record['name_folder'] = name
        name = self.put_helper(self.db.record.put, self.db.record.get, record, ['name_folder', 'rectype'])

    def test_record_put_dict_input(self):
        record = dict(name_folder='The Record Name', rectype='folder')
        self.put_helper(self.db.record.put, self.db.record.get, record, ['name_folder', 'rectype'])

    def test_record_put_norecorddef(self):
        record = dict(name_folder='The Record Name')
        self.assertRaises(ValueError, self.db.record.put, record)

    def test_record_put_invalidrecorddef(self):
        record = dict(name_folder='The Record Name', rectype='no_such_rectype')
        self.assertRaises(ValueError, self.db.record.put, record)

    def test_record_put_invalidparamdef(self):
        record = dict(no_such_param='The Record Name', rectype='folder')
        self.assertRaises(ValueError, self.db.record.put, record)

    def test_user_put_basic_invocation(self):
        un = 'testuser'
        pw = 'testpassword'
        em = 'test@example.com'
        signup_info = dict(
         name_first='first name',
         name_last='last name',
         email=em,
         password=pw,
         password2=pw,
         institution='institution',
         department='department',
         address_street='41463 some street',
         address_city='some city',
         address_state='ME',
         address_zipcode='92293',
         country='some country'
      )

        user = self.db.newuser.new(password=pw, email=em)
        user.setsignupinfo(signup_info)
        self.db.newuser.put(user)
        self.db.newuser.approve(user.name)
        c_user = self.db.user.get(user.name)
        urec = c_user.userrec

        self.assertEqual(user.name, un)
        self.assertEqual(user.email, em)
        signup_info.pop('password')
        signup_info.pop('password2')
        ### shouldn't this be in the user record?
        signup_info.pop('email')
        for key in signup_info.keys():
            self.assertEqual(urec.get(key), signup_info.get(key))

    def test_paramdef_put_dict_input(self):
        paramdef = self.db.paramdef.new(name='testparamdef', vartype='string')
        self.put_helper(self.db.paramdef.put, self.db.paramdef.names, paramdef, ['name', 'vartype'])

    def test_paramdef_put_nonexistentvartype_basic_invocation(self):
        self.assertRaises(ValueError, self.db.paramdef.new, 'testparamdef', 'no_such_vartype')

    def test_paramdef_put_nonexistentvartype_dict_input(self):
        self.assertRaises(ValueError, self.db.paramdef.put, dict(name='testparamdef', vartype='no_such_vartype'))

    def test_paramdef_put_vartypes_validvalue(self):
        paramdef = self.db.paramdef.new(name='testparamdef', vartype='int')
        self.db.paramdef.put(paramdef)

        rec = self.db.record.new(rectype='folder')

        valid_value = 123
        rec['testparamdef'] = valid_value
        self.assertEqual(rec['testparamdef'], valid_value)

        name = self.db.record.put(rec).name
        rec = self.db.record.get(name)
        self.assertEqual(rec['testparamdef'], valid_value)

    def test_paramdef_put_vartypes_invalidvalue(self):
        paramdef = self.db.paramdef.new(name='testparamdef', vartype='int')
        self.db.paramdef.put(paramdef)

        rec = self.db.record.new('folder')
        invalid_value = 'asdasd'

        self.assertRaises(ValueError, rec.__setitem__, 'testparamdef', invalid_value)
        self.assertRaises(ValueError, rec.__setattr__, 'testparamdef', invalid_value)

        name = self.db.record.put(rec).name
        rec = self.db.record.get(name)
        self.assertEqual(rec['testparamdef'], None)

    def test_recorddef_put_basic_invocation(self):
        recorddef = self.db.recorddef.new(name='testrecorddef', mainview='$$name_folder $$address_city')
        self.db.recorddef.put(recorddef)
        rd = self.db.recorddef.get(recorddef.name)
        self.assertEqual(rd.paramsK, set(['name_folder','address_city']))

    def test_record_render(self):
        recorddef = self.db.recorddef.new(name='testrecorddef', mainview='$$name_folder $$address_city')
        self.db.recorddef.put(recorddef)
        rec = self.db.record.new(rectype=recorddef.name)
        rec['name_folder'] = 'Test Folder'
        rec['address_city'] = 'Test Address'
        rec = self.db.record.put(rec)
        r_view = self.db.view(rec.name, viewname='mainview')
        self.assertEqual(r_view, '{name_folder} {address_city}'.format(**rec))

    def test_recorddef_put_invalidname(self):
        self.assertRaises(ValueError, db.recorddef.new, 123123, '')

    def test_recorddef_put_invalidmainview(self):
        self.assertRaises(ValueError, db.recorddef.new, 'testrecorddef', '')

    def test_recorddef_put_change_name(self):
        recorddef = db.recorddef.new(name='testrecorddef', mainview='a mainview')
        self.assertRaises(ValueError, recorddef.__setitem__, 'name', 'new_name')
        self.assertRaises(ValueError, recorddef.__setattr__, 'name', 'new_name')

