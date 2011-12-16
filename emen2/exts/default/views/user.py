# $Id$
import re
import os
import time
import random
import hashlib

import emen2.db.exceptions
import emen2.db.database
from emen2.web.view import View


# Use randomly assigned usernames?
HASH_USERNAME_FORCE = False
HASH_USERNAME = True


@View.register
class User(View):

	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/$")
	def main(self, name=None):
		self.template = "/pages/user.view"
		user = self.db.getuser(name, filt=False)
		self.ctxt["user"] = user
		self.title = "User: %s"%(user.displayname)

		if user.disabled:
			self.ctxt['ERRORS'].append("This user account is disabled")	



	@View.add_matcher("^/user/(?P<name>[\w\- ]+)/edit/$")
	def edit(self, name=None, **kwargs):
		self.template = "/pages/user.edit"
		user = self.db.getuser(name, filt=False)
		self.ctxt["user"] = user
		self.title = "Edit user: %s"%(user.displayname)

		# Security is of course is checked by the database, 
		# this just hides the form itself.
		if self.db.checkcontext()[0] != user.name and not self.ctxt['ADMIN']:
			raise emen2.db.exceptions.SecurityError, "You may only edit your own user page"

		if self.request_method != 'post':
			return

		userrec = kwargs.get('userrec', {})
		if userrec:
			user.userrec.update(userrec)
			self.db.putrecord(user.userrec)
			self.ctxt['NOTIFY'].append('Saved profile.')

		u = kwargs.get('user', {})
		if u:
			user.update(u)
			self.db.putuser(user)
			self.ctxt['NOTIFY'].append('Saved account settings.')
		
		user = self.db.getuser(name)
		self.ctxt['user'] = user
		






@View.register
class Users(View):

	@View.add_matcher(r'^/users/$')	
	def main(self, q=None):
		self.template = "/pages/users"
		self.title = "User directory"
		usernames = self.db.getusernames()

		if q:
			users = self.db.finduser(q)
		else:
			users = self.db.getuser(usernames)
		
		if not users:
			self.template = '/simple'
			self.ctxt['content'] = 'No users found, or insufficient permissions to view user roster.'
			return

		self.ctxt['usernames'] = usernames
		self.ctxt['users'] = users
		self.ctxt['q'] = q or ''


	@View.add_matcher(r'^/users/admin/$', name='admin')	
	def admin(self, sortby="name_last", reverse=0, q=None, **kwargs):
		self.template="/pages/users.admin"
		self.title = 'User administration'
		
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
	def new(self, user=None, userrec=None, **kwargs):
		self.template = '/pages/users.new'
		self.title = 'Account request'
		self.ctxt['kwargs'] = kwargs
		self.ctxt['invalid'] = set()

		# Account settings
		user = user or {}
		# Profile settings
		userrec = userrec or {}

		self.ctxt['user'] = user
		self.ctxt['userrec'] = userrec
		
		# Process form if posted.
		if self.request_method != 'post':
			return
				
		# Always required new user parameters.
		REQUIRED = set(['name_last', 'name_first'])

		# Note: other parameters can be marked as required at the FORM level,
		# using HTML5 'required' attribute. However, industrious users
		# or those using older browsers could easily bypass :)
				
		# Snap off the base user parameters
		email = user.get('email', '').strip()
 		password = user.get('password', None)
		name = user.get('username', '')
		if name and not HASH_USERNAME_FORCE:
			pass
			
		elif HASH_USERNAME:
			# Generate a random username.
			# name = '%s%s%s'%(kwargs.get('name_last',''), time.time(), random.random())
			# name = hashlib.md5(name).hexdigest()
			name = emen2.db.database.getrandomid()

		else:
			# Make a copy of REQUIRED and add name_first and name_last
			name = kwargs.pop('username',None)
			if not name:
				name = '%s%s%s'%(userrec.get('name_first',''), userrec.get('name_middle',''), userrec.get('name_last',''))
				r = re.compile('[\w-]', re.UNICODE)
				name = "".join(r.findall(name)).lower()
		
		try:
			user = self.db.newuser(name=name, password=password, email=email)
			user.setsignupinfo(userrec)
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
		self.title = 'Account requests'

		actions = kwargs.pop('actions', {})
		groups = kwargs.pop('groups', {})

		self.ctxt['actions'] = actions
		# self.ctxt['groups'] = groups

		if self.request_method == 'post':
			# I don't care for this format, but it's a limitation of
			# HTML input elements. 
			reject = set(k for k,v in actions.items() if v=='reject')
			approve = set(k for k,v in actions.items() if v=='approve')
			rejected = []
			approved = []
			if reject:
				rejected = self.db.rejectuser(reject)
			if approve:
				approved = self.db.approveuser(approve)

			# Add the users to all the requested groups.
			# ... do this better in the future.
			for user in approved:
				g = filter(None, groups.get(user.name, []))
				for group in self.db.getgroup(g):
					group.adduser(user.name)
					self.db.putgroup(group)

			if kwargs.get('location'):
				self.headers['Location'] = kwargs.get('location')

		queue = self.db.getqueueduser(self.db.getuserqueue())
		self.ctxt['queue'] = queue

		groupnames = self.db.getgroupnames()
		groupnames -= set(['anon', 'authenticated', 'create'])
		self.ctxt['groups'] = self.db.getgroup(groupnames)




__version__ = "$Revision$".split(":")[1][:-1].strip()
