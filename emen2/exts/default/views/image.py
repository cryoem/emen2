# $Id$
# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View
###


class Image(View):
    __metaclass__ = View.register_view
    __matcher__ = '^/image/(?P<bdo_id>[:\w]+)/$'
    def __init__(self, db=None, p_name=None, bdo_id='', **kwargs):
        View.__init__(self, db=db, mimetype='image/jpg')
        self._bdo_id = bdo_id.split(':').pop()
        self._bin = db.getbinary(self._bdo_id)

    def get_data(self):
        fil = file(self._bin.get('filepath'), 'rb')
        try:
            result = fil.read()
        finally:
            fil.close()
        return result


__version__ = "$Revision$".split(":")[1][:-1].strip()
