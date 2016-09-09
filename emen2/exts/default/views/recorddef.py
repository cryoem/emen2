# $Id: recorddef.py,v 1.30 2013/05/21 16:54:18 irees Exp $
import collections

from emen2.web.view import View



@View.register
class RecordDef(View):

    @View.add_matcher(r'^/recorddef/(?P<name>[^/]*)/new/$')    
    def new(self, name=None, **kwargs):
        if self.request_method == 'post':
            mainview = kwargs.pop('mainview', '')
            views = {}
            view_name = kwargs.pop('view_name', [])
            view_view = kwargs.pop('view_view', [])
            for k,v in zip(view_name, view_view):
                if k and v:
                    views[k] = v
            kwargs['views'] = views
            if kwargs.get('private') == None: kwargs['private'] = False
            recorddef = self.db.recorddef.new(mainview=mainview, name=name)
            recorddef.update(kwargs)
            rd = self.db.recorddef.put(recorddef)
            if rd:
                self.redirect(self.routing.reverse('RecordDef/main', name=rd.name))
                return
                
        self.main(name=name)
        self.template = '/pages/recorddef'
        self.recorddef.parents = set([self.recorddef.name])
        self.recorddef.children = set()
        self.ctxt['edit'] = True
        self.ctxt['new'] = True
        self.title = 'New Protocol based on: %s'%self.recorddef.desc_short




    @View.add_matcher(r'^/recorddef/(?P<name>[^/]*)/edit/$')    
    def edit(self, name=None, **kwargs):
        if self.request_method == 'post':
            views = {}    
            view_name = kwargs.pop('view_name', [])
            view_view = kwargs.pop('view_view', [])
            for k,v in zip(view_name, view_view):
                if k and v:
                    views[k] = v
            kwargs['views'] = views
            if kwargs.get('private') == None: kwargs['private'] = False
            recorddef = self.db.recorddef.get(name)
            recorddef.update(kwargs)
            rd = self.db.recorddef.put(recorddef)
            if rd:
                self.redirect(self.routing.reverse('RecordDef/main', name=rd.name))
                return
                
        self.main(name=name)
        self.template = '/pages/recorddef'
        self.ctxt['edit'] = True
        self.title = 'Edit Protocol: %s'%self.recorddef.desc_short


    @View.add_matcher(r'^/recorddef/(?P<name>[^/]*)/$')    
    def main(self, name=None):
        self.recorddef = self.db.recorddef.get(name, filt=False)
        self.template = '/pages/recorddef'
        self.title = "Protocol: %s"%self.recorddef.desc_short

        parentmap = self.routing.execute('Tree/embed', db=self.db, keytype='recorddef', root=self.recorddef.name, mode='parents', recurse=3)

        users = set()
        users.add(self.recorddef.creator)
        users.add(self.recorddef.modifyuser)
        displaynames = dict((i.name, i.displayname) for i in self.db.user.get(users))

        self.ctxt.update(dict(
            parentmap = parentmap,
            editable = self.recorddef.writable(),
            create = self.db.auth.check.create(),
            recorddef = self.recorddef,
            displaynames = displaynames,
            edit = False,
            new = False,
        ))



@View.register
class RecordDefs(View):

    @View.add_matcher(r'^/recorddefs/name/$')
    def name(self, *args, **kwargs):
        return self.main(action='name', *args, **kwargs)


    @View.add_matcher(r'^/recorddefs/count/$')
    def count(self, *args, **kwargs):
        return self.main(action='count', *args, **kwargs)


    @View.add_matcher(r'^/recorddefs/tree/$')
    def tree(self, action=None, q=None, *args, **kwargs):
        return self.main(action='tree', *args, **kwargs)


    @View.add_matcher(r'^/recorddefs/$')
    def main(self, action=None, q=None):
        recorddefnames = self.db.recorddef.filter(None)
        
        if action == None or action not in ["tree", "name", "count"]:
            action = "tree"

        if q:
            recorddefs = self.db.recorddef.find(q)
            action = "name"
        else:
            recorddefs = self.db.recorddef.get(recorddefnames)

        # Tab Switcher
        pages = collections.OrderedDict()
        pages['tree'] = 'Protocol ontology'
        pages['name'] = 'Protocols by name'
        pages['count'] = 'Protocols by number of records'
        uris = {}
        for k in pages:
            uris[k] = self.routing.reverse('RecordDefs/%s'%k)
        pages.uris = uris
        pages.active = action
        self.ctxt['pages'] = pages

        self.template = '/pages/recorddefs.%s'%action        
        self.title = pages.get(action)

        # Children
        childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="recorddef", root="root", recurse=-1, id='sitemap')

        # Record counts
        count = {}
        if action != 'tree':
            for pd in recorddefs:
                count[pd.name] = len(self.db.record.findbyrectype(pd.name))

        self.ctxt['recorddefnames'] = recorddefnames
        self.ctxt['q'] = q
        self.ctxt['count'] = count
        self.ctxt["recorddefs"] = recorddefs
        self.ctxt["childmap"] = childmap
        self.ctxt['create'] = self.db.auth.check.create()




__version__ = "$Revision: 1.30 $".split(":")[1][:-1].strip()
