# $Id: help.py,v 1.4 2012/07/28 06:31:18 irees Exp $
from emen2.web.view import View

@View.register
class Help(View):

    @View.add_matcher(r'^/help/$')
    def main(self, **kwargs):
        self.title = "Help"
        self.template = "/pages/help"
        
        
__version__ = "$Revision: 1.4 $".split(":")[1][:-1].strip()
