"""
	def newuser(self, name, password, email, ctx=None, txn=None):
	def newgroup(self, name, ctx=None, txn=None):
	def newparamdef(self, name, vartype, ctx=None, txn=None):
	def newrecorddef(self, name, mainview, ctx=None, txn=None):
	def newrecord(self, rectype, inherit=None, ctx=None, txn=None):
	def newbinary(self, ctx=None, txn=None):
"""
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
		self.rec = self.db.putrecord(dict(
			name_folder='Test Name',
			rectype='folder',
			parents=set([0])
		))

	def tearDown(self):
		self.db._aborttxn()
		assert self.db.getrecord(self.rec.name) is None

	def put_helper(self, putter, getter, data, match_keys):
		data1 = putter(data)
		data2 = getter(data1['name'])

		self.assertEqual(data1, data2)
		self.assertEqual(*match_dicts(data, data1, match_keys))
		self.assertEqual(*match_dicts(data, data2, match_keys))
		return data1.name

	def test_putrecord_basic_invocation(self):
		record = self.db.newrecord('folder')
		name = 'The Record Name'
		record['name_folder'] = name
		name = self.put_helper(self.db.putrecord, self.db.getrecord, record, ['name_folder', 'rectype'])

	def test_putrecord_dict_input(self):
		record = dict(name_folder='The Record Name', rectype='folder')
		self.put_helper(self.db.putrecord, self.db.getrecord, record, ['name_folder', 'rectype'])

	def test_putrecord_norecorddef(self):
		record = dict(name_folder='The Record Name')
		self.assertRaises(ValueError, self.db.putrecord, record)

	def test_putrecord_invalidrecorddef(self):
		record = dict(name_folder='The Record Name', rectype='no_such_rectype')
		self.assertRaises(ValueError, self.db.putrecord, record)

	def test_putrecord_invalidparamdef(self):
		record = dict(no_such_param='The Record Name', rectype='folder')
		self.assertRaises(ValueError, self.db.putrecord, record)

	def test_putuser_basic_invocation(self):
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

		user = self.db.newuser(un, pw, em)
		user.setsignupinfo(signup_info)
		self.db.adduser(user)
		self.db.approveuser(user.name)
		c_user = self.db.getuser(user.name)
		urec = c_user.userrec

		self.assertEqual(user.name, un)
		self.assertEqual(user.email, em)
		signup_info.pop('password')
		signup_info.pop('password2')
		### shouldn't this be in the user record?
		signup_info.pop('email')
		for key in signup_info.keys():
			self.assertEqual(urec.get(key), signup_info.get(key))

	def test_putparamdef_dict_input(self):
		paramdef = self.db.newparamdef('testparamdef', 'string')
		self.put_helper(self.db.putparamdef, self.db.getparamdef, paramdef, ['name', 'vartype'])

	def test_putparamdef_nonexistentvartype_basic_invocation(self):
		self.assertRaises(ValueError, self.db.newparamdef, 'testparamdef', 'no_such_vartype')

	def test_putparamdef_nonexistentvartype_dict_input(self):
		self.assertRaises(ValueError, self.db.putparamdef, dict(name='testparamdef', vartype='no_such_vartype'))

	def test_putparamdef_vartypes_validvalue(self):
		paramdef = self.db.newparamdef('testparamdef', 'int')
		self.db.putparamdef(paramdef)

		rec = self.db.newrecord('folder')

		valid_value = 123
		rec['testparamdef'] = valid_value
		self.assertEqual(rec['testparamdef'], valid_value)

		name = self.db.putrecord(rec).name
		rec = self.db.getrecord(name)
		self.assertEqual(rec['testparamdef'], valid_value)

	def test_putparamdef_vartypes_invalidvalue(self):
		paramdef = self.db.newparamdef('testparamdef', 'int')
		self.db.putparamdef(paramdef)

		rec = self.db.newrecord('folder')
		invalid_value = 'asdasd'

		self.assertRaises(ValueError, rec.__setitem__, 'testparamdef', invalid_value)
		self.assertRaises(ValueError, rec.__setattr__, 'testparamdef', invalid_value)

		name = self.db.putrecord(rec).name
		rec = self.db.getrecord(name)
		self.assertEqual(rec['testparamdef'], None)

	def test_putrecorddef_basic_invocation(self):
		recorddef = self.db.newrecorddef('testrecorddef', '$$name_folder $$address_city')
		self.db.putrecorddef(recorddef)
		rd = self.db.getrecorddef(recorddef.name)
		self.assertEqual(rd.paramsK, set(['name_folder','address_city']))

	def test_renderview(self):
		recorddef = self.db.newrecorddef('testrecorddef', '$$name_folder $$address_city')
		self.db.putrecorddef(recorddef)
		rec = self.db.newrecord(recorddef.name)
		rec['name_folder'] = 'Test Folder'
		rec['address_city'] = 'Test Address'
		rec = self.db.putrecord(rec)

		r_view = self.db.renderview(rec.name, viewname='mainview', markup=False)
		self.assertEqual(r_view, '{name_folder} {address_city}'.format(**rec))

	def test_putrecorddef_invalidname(self):
		self.assertRaises(ValueError, db.newrecorddef, 123123, '')

	def test_putrecorddef_invalidmainview(self):
		self.assertRaises(ValueError, db.newrecorddef, 'testrecorddef', '')

	def test_putrecorddef_change_name(self):
		recorddef = db.newrecorddef('testrecorddef', 'a mainview')
		self.assertRaises(ValueError, recorddef.__setitem__, 'name', 'new_name')
		self.assertRaises(ValueError, recorddef.__setattr__, 'name', 'new_name')


