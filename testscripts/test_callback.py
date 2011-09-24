import functools

class View(object):
	def __init__(self, db, request_method, request_headers):
		self.db = db
		self.request_method = request_method
		self.request_headers = request_headers
	
	def main(self, name, action):
		print "View.main ->", name, action
		
		
db = None
request_method = 'get'
request_headers = {}



def make_callback(v, m):
	def cb1(db, request_method, request_headers):
		view = v(db=db, request_method=request_method, request_headers=request_headers)
		def cb2(*args, **kwargs):
			return m(view, *args, **kwargs)
		return cb2
	return cb1
	
callback = make_callback(View, View.main)
result = callback(db, request_method, request_headers)(name='root', action='delete')

