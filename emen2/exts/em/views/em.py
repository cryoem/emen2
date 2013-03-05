# $Id$
import datetime
import time
import tempfile
import os

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
class EMHome(View):

    @View.add_matcher(r'^/$', view='Root', name='main')
    @View.add_matcher(r'^/em/home/$', r'^/db/home/$')
    def main(self, hideinactive=False, sortkey='name', reverse=False):
        self.title = 'Home'
        self.template = '/em/home.main'

        banner = None
        render_banner = ''
        
        if not self.ctxt['USER']:            
            self.template = '/em/home.noauth'
            try:
                banner = self.db.record.get(emen2.db.config.get('bookmarks.banner_noauth'))
                render_banner = self.db.view(banner, viewname="banner")
            except:
                pass
            self.ctxt['banner'] = banner
            self.ctxt['render_banner'] = render_banner
            return

        try:
            banner = self.db.record.get(emen2.db.config.get('bookmarks.banner'))
            render_banner = self.db.view(banner, viewname="banner")
        except:
            pass
            
        self.ctxt['banner'] = banner
        self.ctxt['render_banner'] = render_banner

        # Recent records
        now = datetime.datetime.utcnow().isoformat()+'+00:00'
        since = (datetime.datetime.utcnow() - datetime.timedelta(days=90)).isoformat()+'+00:00'
        q = self.db.plot(
            [['creationtime', '>=', since]], 
            x={'key':'creationtime', 'bin':'day', 'min':since, 'max':now}, 
            y={'stacked':True},
            sortkey='creationtime'
            )            
        self.ctxt['recent_activity'] = q

        # Table
        q_table = self.routing.execute('Query/embed', db=self.db, q={'count':20, 'subset':q['names']}, controls=False)
        self.ctxt['recent_activity_table'] = q_table
        
        
        # Groups and projects
        torender = set()
        def nodeleted(items):
            return filter(lambda x:not x.get('deleted'), items)

        # Groups
        groups = nodeleted(self.db.record.get(self.db.record.findbyrectype('group')))
        groupnames = set([i.name for i in groups])
        torender |= groupnames

        # Top-level children of groups (any rectype)
        groups_children = self.db.rel.children(groupnames)
        projs = set()
        for v in groups_children.values():
            projs |= v
        torender |= projs

        # Get projects, most recent children, and progress reports
        # projects_children = self.db.rel.children(projs, recurse=-1)
        projects_children = {}

        # Get all the recent records we want to display
        recnames = self.db.view(torender)

        # Update context
        self.ctxt['recnames'] = recnames
        self.ctxt['groups'] = groups
        self.ctxt['groups_children'] = groups_children
        self.ctxt['projects_children'] = {}
        
                
        
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

        if format not in ['tif', 'tiff', 'mrc', 'hdf', 'jpg', 'jpeg', 'png']:
            raise ValueError, "Invalid format: %s"%format

        bdo = self.db.binary.get(name)
        img = EMAN2.EMData()
        img.read_image(str(bdo.filepath))
        
        if normalize:
            img.process_inplace("normalize")            
        
        outfile = tempfile.NamedTemporaryFile(delete=False, suffix='.%s'%format)
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
            
