# $Id$
VERSION = '2.1b11'
__version__ = "$Revision$".split(":")[1][:-1].strip()

# Support Python 2.6
import collections
if not hasattr(collections, 'OrderredDict'):
    from .util import orderreddict
