# $Id: home.py,v 1.27 2012/10/18 09:41:40 irees Exp $
import time

import emen2.db.exceptions
import emen2.db.config
from emen2.web.view import View



@View.register
class Home(View):

    #@View.add_matcher(r'^/$', view='Root', name='main')
    #@View.add_matcher(r'^/home/$')
    def main(self):
        self.title = 'Home'
        self.template = '/pages/home'
        
        # Get the banner/welcome message
        bookmarks = {}
        banner = emen2.db.config.get('bookmarks.banner')

        try:
            user, groups = self.db.auth.check.context()
        except (emen2.db.exceptions.AuthenticationError, emen2.db.exceptions.SessionError), inst:
            user = "anonymous"
            groups = set(["anon"])
            self.ctxt["msg"] = str(inst)

        if user == "anonymous":
            banner = bookmarks.get('bookmarks.banner_noauth', banner)

        try:
            banner = self.db.record.get(banner)
            render_banner = self.db.record.render(banner)
        except Exception, inst:
            banner = None
            render_banner = ""

        if user == "anonymous":
            self.template = '/pages/home.noauth'
            return

        


__version__ = "$Revision: 1.27 $".split(":")[1][:-1].strip()
