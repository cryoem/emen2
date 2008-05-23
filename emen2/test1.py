import emen2.emen2config
import g
from emen2.test import *
from emen2.query import *

query = DBQuery(db, ctxid, None)
def main(environ, start_response):
	start_response('200', [('Content-Type', 'text/plain')]);
	return ['hello']

