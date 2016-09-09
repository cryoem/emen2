# $Id: home.py,v 1.30 2013/06/27 06:52:52 irees Exp $
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
class Home(View):

    @View.add_matcher(r'^/$', view='Root', name='main')
    @View.add_matcher(r'^/home/$', r'^/db/home/$')
    def main(self, hideinactive=False, sortkey='name', reverse=False):
        self.title = 'Home'
        self.template = '/pages/home.main'

        banner = None
        render_banner = ''
        
        if not self.ctxt['USER']:            
            self.template = '/pages/home.noauth'
            try:
                banner = self.db.record.get(emen2.db.config.get('bookmarks.banner_noauth'))
                render_banner = self.db.view(banner, viewname="banner", options={'output':'html'})
            except:
                pass
            self.ctxt['banner'] = banner
            self.ctxt['render_banner'] = render_banner
            return

        try:
            banner = self.db.record.get(emen2.db.config.get('bookmarks.banner'))
            render_banner = self.db.view(banner, viewname="banner", options={'output':'html'})
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
        
        # Ok, hold on for a sec. Group "groups" by parent records.
        groups_group = collections.defaultdict(set)
        for k,v in self.db.rel.parents(groupnames).items():
            for v2 in v:
                groups_group[v2].add(k)
        torender |= set(groups_group.keys())

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
        self.ctxt['groups_group'] = groups_group
          