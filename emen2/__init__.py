# $Id$
VERSION = '2.0rc7'
__version__ = "$Revision$".split(":")[1][:-1].strip()

# Support Python 2.6
import collections
if not hasattr(collections, 'OrderredDict'):
	from .util import orderreddict
