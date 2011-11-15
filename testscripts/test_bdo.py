import cStringIO as StringIO
import emen2.db
import emen2.db.handlers
db = emen2.db.opendb(admin=True)

with db:
	for i in range(1000):
		fobj = StringIO.StringIO("Hello, world!")
		f = emen2.db.handlers.EMEN2File(filename='test%s.txt'%i, fileobj=fobj)
		
		handler = emen2.db.handlers.TestTmpHandler([f])
		print handler.extract()
		
		#bdo = db.putbinary(f)
		#print "\n\n--- %s ---"%i
		#print bdo