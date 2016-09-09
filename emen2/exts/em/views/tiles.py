# $Id: tiles.py,v 1.15 2012/10/18 23:34:23 irees Exp $
import os
import pickle
import math
import json

import jsonrpc.jsonutil

import emen2.db.config
from emen2.web.view import View

import emen2.db.handlers

# header[index][slices][tiles][(level, x, y)]


@View.register
class Preview(View):
    @View.add_matcher(r'^/preview/(?P<bid>[^/]*)/(?P<mode>.+)/$')    
    def main(self, bid=None, mode='tiles', **kwargs):
        if bid == None:
            return "No Binary ID supplied."

        # Make sure we can access bdo
        bdo = self.db.binary.get(bid, filt=False)
        filename = bdo.get('filename')
        size = int(kwargs.get('size', 512))
        index = int(kwargs.get('index', 0))
        scale = int(kwargs.get('scale', 1))
        z = int(kwargs.get('z', 0))
        x = int(kwargs.get('x', 0))
        y = int(kwargs.get('y', 0))

        # get_data(self)
        previewpath = emen2.db.binary.Binary.parse(bid).get('previewpath')
        previewpath = '%s.eman2'%(previewpath)

        if not os.path.exists(previewpath):
            status = emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)
            raise Exception, "Building tile..."

        f = file(previewpath, "r")
        header = pickle.load(f)

        if mode == 'header':
            h = header[index]
            data = {
                'nx': h['nx'],
                'ny': h['ny'],
                'nz': h['nz'],
                'maxscale': 8,
                'filename': filename
            }
            f.close()
            return jsonrpc.jsonutil.encode(data)

        h = header[index]['slices'][z]
        key = size
        if mode == 'tiles':
            key = (scale, x, y)

        ret = h[mode][key]

        f.seek(ret[0], 1)
        data = f.read(ret[1])
        f.close()

        if ret[2] == 'jpg':
            self.set_header("Content-Type", "image/jpeg")
        elif ret[2] == 'png':
            self.set_header("Content-Type", "image/png")
        elif ret[2] == 'json':
            self.set_header("Content-Type", "application/json")

        return data
    




__version__ = "$Revision: 1.15 $".split(":")[1][:-1].strip()
