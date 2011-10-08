# $Id$
from emen2.web.view import View

@View.register
class Auth(View):

	# @View.provides('auth_login')
	@View.add_matcher(r'^/auth/login/$')
	def login(self, name=None, pw=None, msg='', errmsg='', location=None, **kwargs):
		self.template = '/auth/login'
		self.title = 'Login'
		location = location or self.ctxt['EMEN2WEBROOT']
		if 'auth' in location or not location:
			location = self.ctxt['EMEN2WEBROOT']

		self.set_context_item("name",name)
		self.set_context_item('location', location)

		ctxid = None
		if name != None:
			ctxid = self.db.login(name, pw, host=self.ctxt['HOST'])
			msg = 'Successfully logged in'

			self.set_header('X-Ctxid', ctxid)
			self.redirect(location or '/')
			# self.set_header('Location', location or '/')

		if msg:
			self.ctxt['NOTIFY'].append(msg)
		if errmsg:
			self.ctxt['ERRORS'].append(errmsg)




	# @View.provides('auth_logout')
	@View.add_matcher(r'^/auth/logout/$')
	def logout(self, msg='', location=None, **kwargs):
		self.template = '/auth/login'
		self.title = 'Logout'
		msg = ''
		errmsg = ''

		location = location or self.ctxt['EMEN2WEBROOT']
		if 'auth' in location or not location:
			location = self.ctxt['EMEN2WEBROOT']

		self.set_context_item('location', location)
		try:
			self.db.logout()
			msg = 'Successfully logged out'
		except Exception, errmsg:
			pass

		self.set_header('Location', location or '/')
		self.set_header('X-Ctxid', '')

		if msg:
			self.ctxt['NOTIFY'].append(msg)
		if errmsg:
			self.ctxt['ERRORS'].append(errmsg)



	@View.add_matcher(r'^/auth/password/change/$', name='password/change')
	def setpassword(self, location=None, **kwargs):
		self.template = '/auth/password.change'
		self.title = "Password Change"
		self.ctxt['location'] = location

		name = kwargs.pop("name",None) or self.db.checkcontext()[0]
		opw = kwargs.pop("opw",None)
		on1 = kwargs.pop("on1",None)
		on2 = kwargs.pop("on2",None)

		msg = ''
		errmsg = ''

		self.ctxt['name'] = name

		if not on1 and not on2:
			pass

		elif on1 != on2:
			errmsg = "New passwords did not match"

		else:
			try:
				self.db.setpassword(opw, on1, name=name)
				msg = "Password changed successfully"
			except Exception, errmsg:
				pass

		if msg:
			self.ctxt['NOTIFY'].append(msg)
		if errmsg:
			self.ctxt['ERRORS'].append(errmsg)



	@View.add_matcher(r'^/auth/password/reset/$', name='password/reset')
	@View.add_matcher(r'^/auth/password/reset/(?P<email>.+)/(?P<secret>\w+)/$', name='password/reset/confirm')
	def resetpassword(self, location=None, email=None, secret=None, newpassword=None, **kwargs):
		self.template = '/auth/password.reset'
		self.title = "Reset Password"
		self.set_context_item('email',email)
		self.set_context_item('secret',secret)
		self.set_context_item('newpassword','')
		self.set_context_item('location',location)
		msg = ''
		errmsg = ''

		if email:
			if secret and newpassword:
				try:
					name = self.db.setpassword(oldpassword=None, newpassword=newpassword, secret=secret, name=email)
					msg = 'The password for your account, %s, has been changed'%name
				except Exception, errmsg:
					pass

			elif secret and not newpassword:
				# errmsg = "No new password given..."
				pass

			else:
				try:
					self.db.resetpassword(email)
					msg = 'Instructions for resetting your password have been sent to %s'%email
				except Exception, errmsg:
					pass

		if msg:
			self.ctxt['NOTIFY'].append(msg)
		if errmsg:
			self.ctxt['ERRORS'].append(errmsg)



	@View.add_matcher(r'^/auth/email/change/$', name='email/change')
	def setemail(self, location=None, **kwargs):
		self.template = '/auth/email.change'
		self.title = "Change Email"
		self.ctxt['location'] = location

		name = kwargs.get("name") or self.db.checkcontext()[0]
		opw = kwargs.get('opw', None)
		email = kwargs.get('email', None)

		self.set_context_item('email',email)
		msg = ''
		errmsg = ''

		if email:
			try:
				ret = self.db.setemail(email, password=opw, name=name)
				msg = 'A verification email has been sent to %s'%email
			except Exception, errmsg:
				pass

		if msg:
			self.ctxt['NOTIFY'].append(msg)
		if errmsg:
			self.ctxt['ERRORS'].append(errmsg)



	@View.add_matcher(r'^/auth/email/verify/(?P<email>.+)/(?P<secret>\w+)/$', name='email/verify')
	def verifyemail(self, location=None, email=None, secret=None, **kwargs):
		self.template = '/auth/email.verify'
		self.title = "Verify Email"
		msg = ''
		errmsg = ''

		if email and secret:
			try:
				ret = self.db.setemail(email, secret=secret)
				msg = "The email address for your account has been changed to %s"%ret
			except Exception, errmsg:
				pass

		if msg:
			self.ctxt['NOTIFY'].append(msg)
		if errmsg:
			self.ctxt['ERRORS'].append(errmsg)



__version__ = "$Revision$".split(":")[1][:-1].strip()
