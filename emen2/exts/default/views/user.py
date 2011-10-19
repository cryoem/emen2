# $Id$
import re
import os
import time
import random
import hashlib

from emen2.web.view import View


# Use randomly assigned usernames?
HASH_USERNAME_FORCE = False
HASH_USERNAME = True


@View.register
class User(View):

	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/$")
	def main(self, name=None):
		self.template = "/pages/user.view"
		self.user = self.db.getuser(name, filt=False)

		if self.user.disabled:
			self.ctxt['ERRORS'].append("This user account is disabled")	

		self.title = "User: %s (%s)"%(self.user.displayname, name)
		self.ctxt["user"] = self.user


	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/edit/$")
	def edit(self, name=None, **kwargs):
		self.main(name=name)
		self.template = "/pages/user.edit"
		
		if self.db.checkcontext()[0] != self.user.name and not self.ctxt['ADMIN']:
			raise emen2.db.exceptions.SecurityError, "You may only edit your own user page"

		self.title = "Profile Editor"


	# @View.add_matcher("^/user/(?P<name>[\w\- ]+)/save/$")
	# def save(self, name=None, action=None, **kwargs):
	# 	self.edit(name=name, **kwargs)
	# 	kw_userrec = kwargs.pop('userrec',None)
	# 	kw_user = kwargs.pop('user', None)
	# 	self.action_save(kw_userrec, kw_user, kwargs)
	# 	self.ctxt['NOTIFY'].append("Changes Saved")
	# 	self.set_context_item("user",self.user)
	# 
	# 
	# #@write
	# def action_save(self, kw_userrec, kw_user, kwargs):
	# 	# for now, only allow edit of either user or userrec
	# 	if kw_userrec:
	# 		orec = self.db.getrecord(self.user.record)
	# 		if orec is None:
	# 			orec = self.db.newrecord("person")
	# 			orec = self.db.putrecord(orec)
	# 			self.user.record = orec.recid
	# 			self.user = self.db.putuser(self.user)
	# 			# self.user = self.db.getuser(self.user)
	# 		for k,v in kw_userrec.items():
	# 			orec[k] = v
	# 
	# 		# of course clever people can edit the records directly,
	# 		# but for convenience we'll require some fields to be filled here:
	# 		for param in ["name_first","name_last"]:
	# 			if orec.get(param) == None:
	# 				raise Exception, "Required item %s empty"%param
	# 
	# 		self.db.putrecord(orec)
	# 
	# 	elif kw_user:
	# 		email = kw_user.get('email')
	# 		disabled = kw_user.get('disabled')
	# 		privacy = kw_user.get('privacy')
	# 
	# 		if privacy != None:
	# 			self.db.setprivacy(privacy, names=self.user.name)
	# 
	# 		if disabled != None:
	# 			disabled = int(disabled)
	# 			if disabled:
	# 				self.db.disableuser(self.user.name)
	# 			else:
	# 				self.db.enableuser(self.user.name)
	# 
	# 
	# 	self.user = self.db.getuser(self.user.name)





@View.register
class Users(View):

	@View.add_matcher(r'^/users/$')	
	def main(self, q=None):
		self.template = "/pages/users"
		self.title = "User Directory"

		if q:
			users = self.db.finduser(q)
		else:
			users = self.db.getuser(self.db.getusernames())
		
		if not users:
			self.template = '/simple'
			self.ctxt['content'] = 'No users found, or insufficient permissions to view user roster.'
			return

		self.set_context_item('users', users)
		self.set_context_item('q', q or '')


	@View.add_matcher(r'^/users/admin/$', name='admin')	
	def admin(self, sortby="name_last", reverse=0, q=None, **kwargs):
		self.template="/pages/users.admin"
		self.title = 'User Management'
		
		if q:
			users = self.db.finduser(q)
		else:
			users = self.db.getuser(self.db.getusernames())

		self.ctxt['args'] = kwargs
		self.ctxt['q'] = q
		self.ctxt['users'] = users
		self.ctxt['sortby'] = sortby
		self.ctxt['reverse'] = reverse






@View.register
class NewUser(View):

	#@write
	@View.add_matcher("^/users/new/$", view='Users', name='new')
	def new(self, **kwargs):
		self.template = '/pages/users.new'
		self.title = 'New User Application'
		self.ctxt['kwargs'] = kwargs
		self.ctxt['invalid'] = set()
		
		# Process form if posted.
		if self.request_method != 'post':
			return
				
		# Always required new user parameters.
		REQUIRED = set(['name_last', 'name_first'])

		# Note: other parameters can be marked as required at the FORM level,
		# using HTML5 'required' attribute. However, industrious users
		# or those using older browsers could easily bypass :)
				
		# Snap off the base user parameters
		email = kwargs.get('email', '').strip()
		op1 = kwargs.pop('op1', None)
		op2 = kwargs.pop('op2', None)
		
		name = kwargs.pop('username', '')
		if name and not HASH_USERNAME_FORCE:
			pass
			
		elif HASH_USERNAME:
			# Generate a random username.
			# name = '%s%s%s'%(kwargs.get('name_last',''), time.time(), random.random())
			# name = hashlib.md5(name).hexdigest()
			name = emen2.db.database.getrandomid()

		else:
			# Make a copy of REQUIRED and add name_first and name_last
			r = set('name_first', 'name_last')
			r |= REQUIRED
			REQUIRED = r
			name = kwargs.pop('username',None)
			if not name:
				name = '%s%s%s'%(kwargs.get('name_first',''), kwargs.get('name_middle',''), kwargs.get('name_last',''))
				r = re.compile('[\w-]', re.UNICODE)
				name = "".join(r.findall(name)).lower()

		
		if op1 != op2:
			self.ctxt['ERRORS'].append('Passwords did not match.')
			self.ctxt['invalid'] |= set(['op1', 'op2'])

		for param in REQUIRED:
			if not kwargs.get(param):
				# self.ctxt['ERRORS'].append('Required value: %s'%param)
				self.ctxt['invalid'].add(param)
				
		# Form is OK, try to create new user.
		if self.ctxt['ERRORS'] or self.ctxt['invalid']:
			return
		
		try:
			user = self.db.newuser(name=name, password=op1, email=email)
			user.setsignupinfo(kwargs)
			self.db.adduser(user)

		except Exception, e:
			self.ctxt['ERRORS'].append('There was a problem creating your account: %s'%e)

		else:
			self.template = "/simple"
			self.ctxt['content'] = '''
				<h1>New User Request</h1>
				<p>
					Your request for a new account is being processed. 
					You will be notified via email when it is approved.
				</p>
				<p>Email: %s</p>
				'''%(user.email)


	@View.add_matcher(r'^/users/queue/$', view='Users', name='queue')	
	def queue(self, action=None, name=None, **kwargs):
		self.template='/pages/users.queue'	
		self.title = 'Users awaiting approval'

		actions = kwargs.pop('actions', {})
		self.ctxt['actions'] = actions

		if self.request_method == 'post':
			# I don't care for this format, but it's a limitation of
			# HTML input elements. I couldn't get the radio buttons 
			# to more closely match the emen2 API.
			reject = set(k for k,v in actions.items() if v=='reject')
			approve = set(k for k,v in actions.items() if v=='approve')
			if reject:
				self.db.rejectuser(reject)
			if approve:
				self.db.approveuser(approve)

			if kwargs.get('location'):
				self.headers['Location'] = kwargs.get('location')


		queue = self.db.getqueueduser(self.db.getuserqueue())
		self.ctxt['queue'] = queue



__version__ = "$Revision$".split(":")[1][:-1].strip()
