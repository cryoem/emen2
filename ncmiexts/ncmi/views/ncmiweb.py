from emen2.web.view import View

@View.register
class NCMIEventsView(View):
        
    @View.add_matcher(r'^/ncmi/events/$')
    def events(self):
        self.title = 'NCMI Events'
        self.template = '/ncmi.events'
                
                
    # Regular expressions can be tricky
    # The regex here goes into the routing table
    # and matches incoming requests
    # with the path:
    #       /ncmi/events/*/
    # The part here: (?P<name>[^/]*)
    # inside the parens is called a capture group
    # Where ?P<name> defines the name of the capture group, here, "name" originally enough
    # and [^/]* defines the the characters matched in the group
    # In this case, the square brackets denote a set of characters that match
    # The * is the "greedy" operator, which will match any repeating # of characters
    # The caret ^ inside the square bracket means "Anything BUT" the following character, here "/"
    # So, any string that does not contain a / is matched
    # For example,
    #   /ncmi/events/123/
    # Will match "name" group to "123"
    # And /ncmi/events/123/456/ will NOT match... this is because the LAST thing in the regex
    # is "$" which means "End of string". Likewise, the ^ at the START of the regex means "Start of string" anchor.
    #
    # The value of the "name" capture group will be passed as the argument "name" to the method below.
    # equivalent to: self.name('123')
    @View.add_matcher(r'^/ncmi/events/(?P<name>[^/]*)/$')
    def event(self, name):
        self.title = 'NCMI Event: %s'%name
        self.template = '/ncmi.event'
        # self.ctxt is a dictionary that is passed to the template.
        self.ctxt['name'] = name
                                