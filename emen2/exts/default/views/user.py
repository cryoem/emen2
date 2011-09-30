# $Id$
import re
import os

import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View



@View.register
class User(View):


	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/$")
	def init(self, name=None):
		self.template = "/pages/user"
		self.user = self.db.getuser(name, filt=False)
		self.name = self.user.name

		displaynames = {}
		for i in self.db.finduser(record=[self.user.record]):
			displaynames[i.name] = i.displayname

		self.admin = self.db.checkadmin()
		try:
			self.admin = user.userrec.writable()
		except:
			pass
			
		if self.user.disabled:
			self.ctxt['ERRORS'].append("This user account is disabled")	

		self.ctxt["admin"] = self.admin
		self.title = "User: %s (%s)"%(self.user.displayname, name)
		self.ctxt["user"] = self.user



	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/edit/$")
	def edit(self, name=None, **kwargs):
		self.init(name=name)
		self.template = "/pages/user.edit"

		if self.db.checkcontext()[0] != self.name and not self.admin:
			raise emen2.db.exceptions.SecurityError, "You may only edit your own user page"

		self.title = "Profile Editor"
		self.set_context_item("admin",self.admin)



	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/save/$")
	def save(self, name=None, action=None, **kwargs):
		self.edit(name=name, **kwargs)
		kw_userrec = kwargs.pop('userrec',None)
		kw_user = kwargs.pop('user', None)
		self.action_save(kw_userrec, kw_user, kwargs)
		self.ctxt['NOTIFY'].append("Changes Saved")
		self.set_context_item("user",self.user)


	#@write
	def action_save(self, kw_userrec, kw_user, kwargs):
		# for now, only allow edit of either user or userrec
		if kw_userrec:
			orec = self.db.getrecord(self.user.record)
			if orec is None:
				orec = self.db.newrecord("person")
				orec = self.db.putrecord(orec)
				self.user.record = orec.recid
				self.user = self.db.putuser(self.user)
				# self.user = self.db.getuser(self.user)
			for k,v in kw_userrec.items():
				orec[k] = v

			# of course clever people can edit the records directly,
			# but for convenience we'll require some fields to be filled here:
			for param in ["name_first","name_last"]:
				if orec.get(param) == None:
					raise Exception, "Required item %s empty"%param

			self.db.putrecord(orec)

		elif kw_user:
			email = kw_user.get('email')
			disabled = kw_user.get('disabled')
			privacy = kw_user.get('privacy')

			if privacy != None:
				self.db.setprivacy(privacy, names=self.name)

			if disabled != None:
				disabled = int(disabled)
				if disabled:
					self.db.disableuser(self.name)
				else:
					self.db.enableuser(self.name)


		self.user = self.db.getuser(self.name)





@View.register
class Users(View):

	@View.add_matcher(r'^/users/$')	
	def init(self, q=None):
		self.template = "/pages/users"
		self.title = "User Directory"

		if q:
			users = self.db.finduser(q)
		else:
			users = self.db.getuser(self.db.getusernames())

		#for user in users:
		#	user.getdisplayname(lnf=True)
		
		if not users:
			self.template = "/simple"
			self.set_context_item("content","""No users found, or insufficient permissions to view user roster.""")
			return

		self.set_context_item("users",users)
		self.set_context_item("q",q or '')




@View.register
class AdminUsers(View):

	@View.add_matcher(r'^/users/admin/$', view='Users', name='admin')	
	def init(self, sortby="name_last", reverse=0, q=None, **kwargs):

		self.template="/pages/users.admin"
		self.update_context(args=kwargs, title="User Management", q=q)

		# u = [i.name for i in self.db.finduser(query=unicode(q))] #[i[0] for i in ]

		try:
			reverse = int(reverse)
		except:
			reverse = 0

		if q:
			users = self.db.finduser(q)
		else:
			users = self.db.getuser(self.db.getusernames())

		admin = self.db.checkadmin()
		self.ctxt.update({"users":users, "admin": admin, "sortby":sortby, "reverse":reverse})





@View.register
class NewUser(emen2.web.view.View):

	#@write
	@View.add_matcher("^/users/new/$", view='Users', name='new')
	def save(self, **kwargs):
		self.template = '/pages/users.new'
		self.title = 'New User Application'
		self.ctxt['kwargs'] = kwargs
		self.ctxt['error'] = ''
		error = ''
		invalid = set()

		signuprequired = set([
			'name_first',
			'name_last',
			'email',
			'password',
			'password2',
			"institution",
			"department",
			"address_street",
			"address_city",
			"address_state",
			"address_zipcode",
			"country"
			])

		for i in signuprequired:
			if not kwargs.get(i):
				invalid.add(i)

		self.ctxt['invalid'] = invalid

		# name = kwargs.get('name_first','')+kwargs.get('name_last','')
		name = kwargs.get('name','').strip().lower()
		email = kwargs.get("email", '').strip()

		password = kwargs.pop("password", '')
		password2 = kwargs.pop('password2', '')
		if password != password2:
			self.ctxt['error'] = "Please check that the passwords match"
			self.ctxt['invalid'] |= set(['password', 'password2'])
			return

		try:
			user = self.db.newuser(name=name, password=password, email=email)
			user.setsignupinfo(kwargs)
		except Exception, e:
			self.ctxt['error'] = "There was a problem creating your account: %s"%e

		else:
			self.db.adduser(user)
			self.template = "/simple"
			self.ctxt['content'] = '''
			<h1>New User Request</h1>
			<p>Your request for a new account is being processed. You will be notified via email when it is approved.</p>
			<p>Account name: %s</p>
			<p>Email: %s</p>
			'''%(user.name,user.email)






@View.register
class UserQueue(emen2.web.view.View):

	@View.add_matcher(r'^/users/queue/$', view='Users', name='queue')	
	def init(self, action=None, name=None, **kwargs):
		self.template='/pages/users.queue'

		admin_queue = {}
		for i in self.db.getuserqueue():
			admin_queue[i]=self.db.getqueueduser(i)

		self.set_context_items({"admin_queue":admin_queue})


__version__ = "$Revision$".split(":")[1][:-1].strip()
