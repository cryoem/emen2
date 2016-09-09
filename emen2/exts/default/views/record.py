# $Id: record.py,v 1.94 2013/06/20 23:05:53 irees Exp $
import urllib
import time
import collections

import jsonrpc

import emen2.db.exceptions
import emen2.util.listops as listops
import emen2.web.responsecodes
from emen2.web.view import View

class RecordNotFoundError(emen2.web.responsecodes.NotFoundError):
    title = 'Record not Found'
    msg = 'Record %s not found'



@View.register
class Record(View):
    
    @View.add_matcher(r'^/record/(?P<name>[^/]*)/$')
    def main(self, name=None, children=True, parents=True, sibling=None, viewname="mainview", **kwargs):
        """Main record rendering."""
        # Get record..
        self.rec = self.db.record.get(name, filt=False)
        recnames = self.db.view([name])
        self.title = recnames.get(self.rec.name, self.rec.name)

        # Look for any recorddef-specific template.
        template = '/record/rectypes/%s'%self.rec.rectype
        try:
            emen2.db.config.templates.get_template(template)
        except:
            template = '/record/rectypes/root'
        self.template = template

        # Render main view
        rendered = self.db.view(name, viewname=viewname, options={'output':'html', 'markdown':True})
        rendered_edit = self.db.view(name, viewname=viewname, options={'output':'form', 'markdown':True, 'name': self.rec.name})
        
        # Access tags
        accesstags = []
        if self.rec.get('deleted'):
            accesstags.append('Hidden record')
        if 'publish' in self.rec.get('groups',[]):
            accesstags.append('Published data')
        if 'authenticated' in self.rec.get('groups',[]):
            accesstags.append('All users')
        if 'anon' in self.rec.get('groups', []):
            accesstags.append('Anonymous access')
        self.ctxt['accesstags'] = accesstags

        # User display names
        users = self.db.user.get([self.rec.get('creator'), self.rec.get('modifyuser')])

        # Parent map
        parentmap = self.routing.execute('Tree/embed', db=self.db, root=self.rec.name, mode='parents', recurse=-1, expandable=False)

        # Children
        children = self.db.record.get(self.rec.children)
        children_groups = collections.defaultdict(set)
        for i in children:
            children_groups[i.rectype].add(i)

        # Siblings
        if sibling == None:
            sibling = self.rec.name
        siblings = self.db.rel.siblings(sibling)

        # Get RecordDefs
        recdef = self.db.recorddef.get(self.rec.rectype)
        recdefs = [recdef] + self.db.recorddef.get(children_groups.keys())

        # Pages -- a deprecated UI element. 
        recdefs_d = dict([i.name, i] for i in recdefs)
        pages = collections.OrderedDict()
        pages.uris = {}
        pages['main'] = self.title
        pages.uris
        pages.uris['main'] = self.routing.reverse('Record/main', name=self.rec.name)
        for k,v in children_groups.items():
            pages[k] = "%s (%s)"%(recdefs_d.get(k,dict()).get('desc_short', k),len(v))
            pages.uris[k] = self.routing.reverse('Record/children', name=self.rec.name, childtype=k)    
    
        # Update context
        self.ctxt.update(
            tab = "main",
            rec = self.rec,
            children = children,
            recdef = recdef,
            recdefs = recdefs,
            users = users,
            recnames = recnames,
            parentmap = parentmap,
            edit = False,
            create = self.db.auth.check.create(),
            rendered = rendered,
            rendered_edit = rendered_edit,
            viewname = viewname,
            sibling = sibling,
            siblings = siblings,
            table = "",
            pages = pages
        )    
        
    
    @View.add_matcher(r'^/record/(?P<name>[^/]*)/edit/$', write=True)
    def edit(self, name=None, _format=None, **kwargs):
        self.main(name=name, **kwargs)
        if self.request_method not in ['post', 'put']:
            self.ctxt["tab"] = "edit"
            self.ctxt["edit"] = True
            return

        # Get the record
        if not self.rec.writable():
            raise emen2.db.exceptions.SecurityError, "No write permission for record %s"%self.rec.name

        # Update the record
        if kwargs:
            self.rec.update(kwargs)
            self.rec = self.db.record.put(self.rec)

        for f in self.request_files:
            param = f.get('param', 'file_binary')
            bdo = self.db.binary.put(f)
            self.db.binary.addreference(self.rec.name, param, bdo.name)

        # Redirect
        # IMPORTANT NOTE: Some clients (EMDash) require the _format support below as part of the REST API.        
        self.redirect(self._redirect or self.routing.reverse('Record/main', name=self.rec.name))
        if _format == "json":
            return jsonrpc.jsonutil.encode(self.rec)


    @View.add_matcher(r'^/record/(?P<name>[^/]*)/edit/attachments/$', name='edit/attachments', write=True)
    def edit_attachments(self, name=None, **kwargs):
        self.edit(name=name, **kwargs)
        self.redirect(self.routing.reverse('Record/main', name=self.rec.name, anchor='attachments'))


    @View.add_matcher(r'^/record/(?P<name>[^/]*)/edit/relationships/$', name='edit/relationships', write=True)
    def edit_relationships(self, name=None, **kwargs):
        # ian: todo: Check orphans, show orphan confirmation page
        self.edit(name=name, **kwargs)
        self.redirect(self.routing.reverse('Record/main', name=self.rec.name, anchor='relationships'))


    @View.add_matcher(r'^/record/(?P<name>[^/]*)/edit/permissions/$', name='edit/permissions', write=True)
    def edit_permissions(self, name=None, permissions=None, groups=None, action=None, filt=True):
        self.rec = self.db.record.get(name)
        permissions = permissions or {}
        groups = groups or []
        users = set()
        if hasattr(permissions, 'items'):
            for k,v in permissions.items():
                users |= set(listops.check_iterable(v))
        else:
            for v in permissions:
                users |= set(listops.check_iterable(v))

        if self.request_method != 'post':
            return
            
        if action == 'add':
            self.db.record.setpermissionscompat(names=self.rec.name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt)

        elif action == 'remove':
            self.db.record.setpermissionscompat(names=self.rec.name, recurse=-1, removeusers=users, removegroups=groups, filt=filt)

        elif action == 'overwrite':
            self.db.record.setpermissionscompat(names=self.rec.name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt, overwrite_users=True, overwrite_groups=True)

        else:
            self.rec['groups'] = groups
            self.rec['permissions'] = permissions
            self.rec = self.db.record.put(self.rec)

        self.redirect(self.routing.reverse('Record/main', name=self.rec.name, anchor='permissions'))


    @View.add_matcher(r'^/record/(?P<name>[^/]*)/new/(?P<rectype>[^/]*)/$', write=True)
    def new(self, name=None, rectype=None, _redirect=None, _format=None, **kwargs): 
        """Create a new record."""
        self.main(name=name)
    
        newrec = self.db.record.new(rectype=rectype, inherit=[self.rec.name])
        if self.request_method not in ['post', 'put']:
            self.template = '/record/record.new'
            viewname = 'mainview'
            recdef = self.db.recorddef.get(newrec.rectype)
            rendered = self.db.view(newrec, viewname=viewname)
            self.title = 'New %s'%(recdef.desc_short)
            self.ctxt.update(
                tab = 'new',
                newrec = newrec,
                viewname = viewname,
                rendered = rendered
            )
            return

        # Save the new record
        newrec.update(kwargs)
        newrec = self.db.record.put(newrec)

        for f in self.request_files:
            param = f.get('param', 'file_binary')
            bdo = self.db.binary.put(f)
            self.db.binary.addreference(newrec.name, param, bdo.name)

        # IMPORTANT NOTE: Some clients (EMDash) require the _format support below as part of the REST API.
        self.redirect(_redirect or self.routing.reverse('Record/main', name=newrec.name), content="Your changes were saved.")
        if _format == "json":
            return jsonrpc.jsonutil.encode(newrec)


    @View.add_matcher(r'^/record/(?P<name>[^/]*)/query/$')
    @View.add_matcher(r'^/record/(?P<name>[^/]*)/query/(?P<path>.*)/$')
    def query(self, name=None, path=None, q=None, c=None, **kwargs):
        self.main(name=name)
    

    # @View.add_matcher(r'^/record/(?P<name>[^/]*)/query/(?P<path>.*)/attachments/$')
    @View.add_matcher(r'^/record/(?P<name>[^/]*)/query/attachments/$')
    def query_attachments(self, name=None, path=None, q=None, c=None, **kwargs):
        self.main(name=name)
        self.template = '/record/record.query.attachments'
        # Look up all the binaries
        children = self.db.rel.children(self.rec.name, recurse=-1)
        bdos = self.db.binary.find(record=children, count=0)
        if len(bdos) > 100000 and not confirm:
            raise Exception, "More than 100,000 files returned. Please see the admin if you need to download the complete set."

        records = set([i.record for i in bdos])
        users = set([bdo.get('creator') for bdo in bdos])
        users = self.db.user.get(users)
        # self.ctxt['tab'] = 'attachments'
        self.ctxt['users'].extend(users)
        self.ctxt['recnames'].update(self.db.view(records))
        self.ctxt['bdos'] = bdos
    
    
    @View.add_matcher('^/record/(?P<name>[^/]*)/children/$')
    def children_map(self, name=None):
        self.main(name=name)
        self.template = '/record/record.tree'
        childmap = self.routing.execute('Tree/embed', db=self.db, root=self.rec.name, mode='children', recurse=2, expandable=True)
        self.ctxt['childmap'] = childmap


    @View.add_matcher('^/record/(?P<name>[^/]*)/children/(?P<childtype>\w+)/$')
    def children(self, name=None, childtype=None):
        """Main record rendering."""
        self.main(name=name)

        # Child table
        c = [['children', '==', self.rec.name], ['rectype', '==', childtype]]
        query = self.routing.execute('Query/embed', db=self.db, c=c, parent=self.rec.name, rectype=childtype)

        # Update context
        self.ctxt['table'] = query
        self.ctxt['tab'] = 'children-%s'%childtype
        self.ctxt['childtype'] = childtype
        self.ctxt["pages"].active = childtype # Show the active tab -- this might go away at some point.


    @View.add_matcher("^/record/(?P<name>[^/]*)/hide/$", write=True)
    def hide(self, name=None, confirm=False, childaction=None):
        """Main record rendering."""
        self.main(name=name)
        self.template = "/record/record.hide"

        if self.request_method != 'post' or not confirm:
            orphans = self.db.record.findorphans([self.rec.name])
            children = self.db.rel.children(self.rec.name, recurse=-1)
            self.ctxt['confirm'] = confirm
            self.ctxt['orphans'] = orphans
            return

        self.db.record.hide(self.rec.name, childaction=childaction)
        self.redirect(self.routing.reverse('Record/main', name=self.rec.name))



    @View.add_matcher(r'^/record/(?P<name>[^/]*)/history/$')
    @View.add_matcher(r'^/record/(?P<name>[^/]*)/history/(?P<revision>.*)/', name='history/revision')
    def history(self, name=None, simple=False, revision=None):
        """Revision/history/comment viewer"""
        self.main(name=name, parents=True, children=True)
        self.template = "/record/record.history"

        if revision:
            revision = revision.replace("+", " ")

        users = set()
        paramdefs = set()
        users.add(self.rec.get('creator'))
        users.add(self.rec.get('modifyuser'))
        for i in self.rec.get('history',[]) + self.rec.get('comments',[]):
            users.add(i[0])
        for i in self.rec.get('history', []):
            paramdefs.add(i[2])

        users = self.db.user.get(users)
        paramdefs = self.db.paramdef.get(paramdefs)

        # Update context
        # self.ctxt['tab'] = 'history'
        self.ctxt['users'] = users
        self.ctxt['users_d'] = emen2.util.listops.dictbykey(users, 'name') # do this in template
        self.ctxt['paramdefs'] = paramdefs
        self.ctxt['paramdefs_d'] = emen2.util.listops.dictbykey(paramdefs, 'name') # do this in template
        self.ctxt['simple'] = simple
        self.ctxt['revision'] = revision


    @View.add_matcher("^/record/(?P<name>[^/]*)/email/$")
    def email(self, name=None):
        """Email referenced users."""
        self.main(name=name)
        self.template = "/record/record.email"

        pds = self.db.paramdef.find(record=self.rec.keys())
        users_ref = set()
        for i in pds:
            v = self.rec.get(i.name)
            if not v:
                continue
            if i.vartype == "user":
                if i.iter:
                    users_ref |= set(v)
                else:
                    users_ref.add(v)

        users_permissions = set()
        for v in self.rec.get('permissions'):
            users_permissions |= set(v)

        emailusers = self.db.user.get(users_ref | users_permissions)
        self.ctxt['emailusers'] = emailusers


    @View.add_matcher(r'^/record/(?P<name>[^/]*)/publish/$', write=True)
    def publish(self, name=None, state=None):
        self.main(name=name)

        # Get the items
        names = self.db.rel.children(self.rec.name, recurse=-1)
        names.add(self.rec.name)        

        recs = self.db.record.get(names)
        recs_d = emen2.util.listops.dictbykey(recs)
        state = set(map(unicode, state or [])) & names

        # Find published items
        published = set()
        for rec in recs:
            if 'publish' in rec.groups:
                published.add(rec.name)
        self.ctxt['published'] = published
        
        if self.request_method != 'post':
            self.template = '/record/record.publish'
            childmap = self.routing.execute('Tree/embed', db=self.db, root=self.rec.name, mode='children', recurse=2)
            self.ctxt['childmap'] = childmap
            # self.ctxt['tab'] = 'publish'
            return

        # Process form data
        add = state - published
        remove = published - state
        commit = []            
        for i in remove:
            recs_d[i].removegroup('publish')
            commit.append(recs_d[i])
        for i in add:
            recs_d[i].addgroup('publish')
            commit.append(recs_d[i])
            
        recs = self.db.record.put(commit)
        self.redirect(self.routing.reverse('Record/publish', name=self.rec.name))

        



@View.register
class Records(View):
    
    @View.add_matcher(r"^/records/$")
    def main(self, root="0", removerels=None, addrels=None, **kwargs):
        kwargs['recurse'] = kwargs.get('recurse', 2)
        childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="record", root=root, recurse=kwargs.get('recurse'), id='sitemap')
        self.template = '/pages/records.tree'
        self.title = 'Record relationships'
        self.ctxt['root'] = root
        self.ctxt['childmap'] = childmap
        self.ctxt['create'] = self.db.auth.check.create()


    @View.add_matcher(r"^/records/edit/relationships/$", write=True)
    def edit_relationships(self, root="0", removerels=None, addrels=None, **kwargs):
        self.title = 'Edit record relationships'
        if self.request_method != 'post':
            kwargs['recurse'] = kwargs.get('recurse', 2)
            childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="record", root=root, recurse=kwargs.get('recurse'), id='sitemap')
            self.template = '/pages/records.tree.edit'
            self.ctxt['root'] = root
            self.ctxt['childmap'] = childmap
            self.ctxt['create'] = self.db.auth.check.create()
            return
            
        self.db.rel.relink(removerels=removerels, addrels=addrels)
        self.redirect('%s/records/edit/relationships/?root=%s'%(self.ctxt.root, root), title=self.title, content="Your changes were saved.")

    @View.add_matcher("^/records/edit/$", write=True)
    def edit(self, *args, **kwargs):
        redirect = kwargs.pop('_redirect', None)
        comments = kwargs.pop('comments', '')
        if self.request_method != 'post':
            return

        for k,v in kwargs.items():
            v['name'] = k

        recs = self.db.record.put(kwargs.values())
        if comments:
            for rec in recs:
                rec.addcomment(comments)
            self.db.record.put(recs)

        if redirect:
            self.redirect(redirect)
            return

        self.simple(content="Saved %s records."%(len(recs)))







__version__ = "$Revision: 1.94 $".split(":")[1][:-1].strip()
