# $Id$
__version__ = "$Revision$".split(":")[1][:-1].strip()
__version__ = '2.1b11'

# Support Python 2.6
import collections
if not hasattr(collections, 'OrderredDict'):
    from .util import orderreddict
