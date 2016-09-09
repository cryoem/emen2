# $Id: em.py,v 1.50 2013/06/27 06:52:52 irees Exp $
import datetime
import time
import tempfile
import os
import collections

import twisted.web.static

import emen2.db.exceptions
import emen2.db.config
import emen2.db.log
from emen2.web.view import View




@View.register
class EMEquipment(View):
    @View.add_matcher(r'^/em/equipment/(?P<name>[^/]*)/$')
    def main(self, name, **kwargs):
        self.title = 'Equipment'
        self.template = '/em/project.main'

    @View.add_matcher(r'^/em/equipment/new/(?P<rectype>[^/]*)/$')
    def new(self, rectype, **kwargs):
        self.title = 'New Equipment'
        self.template = '/em/project.new'
        
      
        
@View.register
class EMAN2Convert(View):
    contentTypes = twisted.web.static.loadMimeTypes()
    contentEncodings = {
            ".gz" : "gzip",
            ".bz2": "bzip2"
            }

    defaultType = 'application/octet-stream'    
    return_file = None
    
    @View.add_matcher(r'^/eman2/(?P<name>.+)/convert/(?P<format>\w+)/$', r'^/eman2/(?P<name>.+)/convert/$')
    def convert(self, name, format, normalize=False):
        import EMAN2

        if format not in ['tif', 'tiff', 'tif8', 'mrc', 'hdf', 'jpg', 'jpeg', 'png']:
            raise ValueError, "Invalid format: %s"%format

        depth = None
        if format in ['tif8']:
            depth = 8
            format = 'tif'

        bdo = self.db.binary.get(name)
        img = EMAN2.EMData()
        img.read_image(str(bdo.filepath))
        
        if normalize:
            img.process_inplace("normalize")            
        
        outfile = tempfile.NamedTemporaryFile(delete=False, suffix='.%s'%format)

        if depth == 8:
            img['render_min'] = -1
            img['render_max'] = 256
            img.write_image(str(outfile.name), -1, EMAN2.EMUtil.ImageType.IMAGE_UNKNOWN, False, None, EMAN2.EMUtil.EMDataType.EM_UCHAR, False)
        else:            
            img.write_image(str(outfile.name))

        filename = os.path.splitext(bdo.filename)[0]
        filename = '%s.%s'%(filename, format)
        return filename, outfile.name

    def render_result(self, result, request, t=0, **_):
        filename, filepath = result
        mimetype, encoding = twisted.web.static.getTypeAndEncoding(filename, self.contentTypes, self.contentEncodings, self.defaultType)

        fsize = os.stat(filepath).st_size
        f = open(filepath)

        request.setHeader('Content-Disposition', 'attachment; filename=%s'%filename.encode('utf-8'))
        request.setHeader('Content-Length', str(fsize))
        request.setHeader('Content-Type', mimetype)
        request.setHeader('Content-Encoding', encoding)

        a = twisted.web.static.NoRangeStaticProducer(request, f)
        a.start()

        try:
            emen2.db.log.info("Removing temporary file: %s"%filepath)
            os.remove(filepath)
        except:
            emen2.db.log.error("Couldn't remove temporary file: %s"%filepath)
            
