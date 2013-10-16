import os
import pickle
import math
import json

import jsonrpc.jsonutil

import emen2.db.config
from emen2.web.view import View

import emen2.db.handlers

# header[index][slices][tiles][(level, x, y)]
class BuildingTileException(Exception):
    pass

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

        previewpath = emen2.db.binary.parse(bdo.creationtime, bdo.name)['previewpath']
        previewpath = '%s.eman2'%(previewpath)

        if not os.path.exists(previewpath):
            status = emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)
            raise BuildingTileException("Begin building tiles...")

        f = file(previewpath, "r")
        header = pickle.load(f)
        if mode == 'header':
            # Max Scale is 
            
            h = header[index]
            # This is obviously wrong and complicated. Come back and fix it.
            maxscale = 2**math.ceil(math.log((max(h['nx'], h['ny']) / 512.0), 2))
            data = {
                'nx': h['nx'],
                'ny': h['ny'],
                'nz': h['nz'],
                'maxscale': maxscale,
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

