# $Id$
#!/usr/bin/python
# Edward Langley
# Processes a Schema definition and generates
# RecordDefs
'''\
Input syntax:

Param Definition:
    $Param_name (Param_type) #Short Description
  or
    $Param_name (Param_type) #Short Description:
        Long Description

Record Definition:
    @Recorddef_name:
        >mainview
        #tabular view
        ?default view
		  N recname view
        ---
'''

from string import Template
import re

# Match patterns
PARAM_SHORT = r'^\$(?P<p_name>\w+) \((?P<type>\w+)\) [#](?P<desc_short>[^:\n]+)$'
PARAM_LONG =  r'^\$(?P<p_name>\w+) \((?P<type>\w+)\) [#](?P<desc_short>[^:]+):$'
PARAM_LONG_CONT = r'^(?P<desc_long>[^\n]+)$'
RECORD_DEF_NAME = r'^\@(?P<r_name>\w+):'
RECORD_DEF_MAIN_VIEW = r'^[>](?P<mainview>.+)$'
RECORD_DEF_TAB_VIEW = r'^[#](?P<tabularview>[^\n]+)$'
RECORD_DEF_DEF_VIEW = r'^[?](?P<defaultview>[^\n]+)$'
RECORD_DEF_RECNAME_VIEW = r'^[N] (?P<defaultview>[^\n]+)$'
RECORD_DEF_END = r'^[-]{3}.+$'
BLANK_LINE = r'^[\s]*$'

#Token templates
SHORT_PARAM_TEMPLATE = """
#begin parameter: ${p_name}
${p_name} =  db.database.ParamDef()
${p_name}.name = '${p_name}'
${p_name}.vartype = '${type}'
${p_name}.desc_short = '''${desc_short}'''
db.addparamdef(${p_name},ctxid)
#end parameter: ${p_name}\
"""

LONG_PARAM_TEMPLATE = """
#begin parameter: ${p_name}
${p_name} =  db.database.ParamDef()
${p_name}.name = '${p_name}'
${p_name}.vartype = '${type}'
${p_name}.desc_short = '''${desc_short}'''\
"""

LONG_PARAM_CONT_TEMPLATE = """\
${p_name}.desc_long = '${desc_long}'
db.addparamdef(${p_name},ctxid)
#end parameter: ${p_name}\
"""

RECORD_DEF_TEMPLATE = """
#begin record definition: ${r_name}
${r_name} = db.database.RecordDef()
${r_name}.name = '${r_name}'\
"""

RECORD_DEF_MAINVIEW_TEMPLATE = '''\
${r_name}.mainview = """${mainview}"""
'''

RECORD_DEF_TABULARVIEW_TEMPLATE = '''\
${r_name}.views['tabularview'] = """${tabularview}"""
'''

RECORD_DEF_DEFAULTVIEW_TEMPLATE = '''\
${r_name}.views['defaultview'] = """${defaultview}"""
'''

RECORD_DEF_RECNAMEVIEW_TEMPLATE = '''\
${r_name}.views['recname'] = """${defaultview}"""
'''

RECORD_DEF_END_TEMPLATE = '''\
db.addrecorddef(${r_name},ctxid)
#end record definition: ${r_name}
'''
class AbstractException(Exception): pass

class PrettyPrinter(object):
    def __init__(self): raise AbstractException('Do not use this class')
    def prnt(self, obj, ind=0): pass
    def __call__(self,obj): self.prnt(obj)

class HierchPrinter(PrettyPrinter):
    def __init__(self): pass
    def prnt(self,obj,indent=0):
        for i in obj:
            if hasattr(i, 'split'):
               print '\t'*(indent), i
            else:
               self.prnt(i, indent+1)

class MatchPrinter(PrettyPrinter):
    def __init__(self): pass
    def prnt(self,obj, ind=0):
        try:
            print '  '*ind,obj.name
            for i in obj._Match__ctxt:
                self.prnt(i, ind+1)
        except:
            for i in obj:
                self.prnt(i, ind)

class TokenClass(object):
    registry = {}
    @classmethod
    def get_tok_class(cls, name):
        return cls.registry[name]
    def __init__(self, name, template):
        self.registry[name] = self
        self.__tmpl = Template(template)
    def set_template(self, template):
        self.__tmpl = template
    def render(self, args):
        return self.__tmpl.safe_substitute(args)

class Token(object):
    def __init__(self, name, varname='<varname>', **kwargs):
        self.__name = name
        self.__args = {'varname': varname}
        self.__args.update(kwargs)
        self.__tokclass = TokenClass.get_tok_class(name)
    def __unicode__(self):
        result = [u'<Token name="%s"' % self.__name]
        for x,y in self.__args.items():
		      result.append(unicode("%s = %s" % (x,y)))
        result.append(u'</Token>')
        return unicode.join(u'\n', result)
    __str__ = __unicode__
    def __repr__(self):
        return "<Token %s: %s>" % (self.__name, str.join(',',self.__args.keys()) )
    def __getitem__(self, name):
        return self.__args.get(name, None)
    def modify_item(self, name, value):
        '''appends value to the item'''
        res = self.__args[name]
        self.__args[name] = res + value
    def keys(self):
        return self.__args.keys()
    def name(self):
        return self.__name
    def render(self):
        return self.__tokclass.render(self.__args).rstrip()

class HierchList(list):
    def __init__(self, *args):
        self.__parent = None
        list.__init__(self, *args)
    def __repr__(self):
        return 'HierchList('+list.__repr__(self)+')'
    __str__ = __repr__
    __unicode__ = __repr__
    def set_parent(self, hier):
        self.__parent = hier
    def get_parent(self):
        return self.__parent
    parent = property(get_parent,set_parent)
    def append_child(self, value):
        self.append(value)
        value.parent = self

class MatchContext(list):
    def __init__(self, owner=None, *args):
        self.__parent = owner
        list.__init__(self, *args)
    def __repr__(self):
        return 'MatchContext(['+list.__repr__(self)+'])'
    def add_match(self, match, pos=-1):
        if self.owner != None:
            match.p_ctxt = self.owner
        else:
            match.set_parent_context(self)
        if pos != -1:
            self.append(match)
        else:
            self.insert(pos, match)
    def get_owner(self):
        return self.__parent
    owner = property(get_owner)

class Match(object):
    '''A Class which stores a regular expression and a context to switch to if that expression matches'''
    def __init__(self, name, pattern, shared=False):
        self.__p_ctxt = None
        self.__parent = None
        self.__ctxt = MatchContext(self)
        self.__name = name
        self.__pattern = re.compile(pattern)
        self.__shared = shared
        self.groupdict = {}
    def is_shared(self):
        return self.__shared
    shared = property(is_shared)
    def __repr__(self):
        return '<Match: %s>' % self.name
    def match(self, stri):
        if self.__parent:
            self.groupdict.update(self.__parent.groupdict)
        result = self.__pattern.match(stri)
        if result:
            self.groupdict.update(result.groupdict())
            self.groupdict.update(
            result.groupdict(
              self.groupdict.get('varname', None)
            )
          )
        return result
    def append(self, match):
        match.name # validate object
        self.__ctxt.add_match(match)
        if match.shared:
            for i in self.__ctxt:
                if i.context:
                    i.append(match)
    def set_context(self, ctxt):
        self.__ctxt = ctxt
    def get_context(self):
        return self.__ctxt
    context = property(get_context,set_context)
    def get_parent_context(self):
        if self.__parent != None:
            return self.__parent.context
        elif self.__p_ctxt != None:
            return self.__p_ctxt
        return None
    def set_parent_context(self, val):
        try:
            self.__p_ctxt = val.context
            self.__parent = val
        except:
            self.__p_ctxt = val
        print self.__name,':',self.__parent
    p_ctxt = property(get_parent_context, set_parent_context)
    def __g_name(self):
        return self.__name
    name = property(__g_name)

class Parser(object):
    def __init__(self, fd):
        self.finfo = fd.readlines()
        self.__fidx = 0
        self.__ctxt = MatchContext()

    def add_match(self, match, pos=-1):
        self.__ctxt.add_match(match, pos)

    def get_line(self):
        '''get and preprocess the current line

        returns the line and its indent'''
        if self.__fidx >= len(self.finfo): return (None, None) #Has the file ended?
        result = self.finfo[self.__fidx].rstrip().expandtabs(1) #rstrip line and expand its tabs
        indent = 0                          #calculate indent
        for i in result.split(' '):
            if i != '': break
            indent += 1
        return result, indent       #returns (the line, the indent of the line)

    def get_next_line(self):
        self.__fidx += 1
        return self.get_line()

    def tokenize_block(self, block):
        '''loop through a processed block and convert the matches to tokens'''
        result = []
        gdict = {}
        for i in block:
            try:
                matcher = i['matcher']
                #match = i['match']
                gdict = matcher.groupdict
                result.append(Token(matcher.name, **gdict))
            except:
                print 'Error: \nlast groupdict = %s\nblock = %s\n i = %s' % (gdict, block, i)
                raise
        return result

    def process_block(self, block, ctxt=None):
        '''process the lines in a block'''
        result = []
        c_context = ctxt or self.__ctxt
        for i in block: #loop through block
            if type(i) == str: #is line a string?
                result.append(self.process_line(i, c_context)) #yes -- process line
            else:
                result.extend(self.process_block(i, result[-1]['matcher'].context)) #no -- change contexts and process block
        return result

    def get_block(self, ind=0):
        '''get a block (recursuve function)

          a block is defined as one line with indent == 0
          and any lines below it with an indent > 0
          '''
        indent = ind
        res = HierchList()
        line = None
        first = True
        while indent >= ind:
            tmp = self.get_line()
            if tmp: line, indent = tmp  #get the line
            else: break #???
            if not first:
                if indent ==0: # if it is not the first line received and the line is not indented
                    break          # quit
            if (indent == ind): # if indent has not changed strip and append to the result
                res.append(self.get_continuation(line.strip()))
                self.__fidx += 1 # go to the next line
            elif  indent > ind: # otherwise recurse with new indent
                res.append_child(self.get_block(indent))
            if first:
                first = False
        return res

    def get_continuation(self, line):
        '''concatenate all lines ending with a \\'''
        tmp = [line]
        if len(tmp[-1]) == 0:
            return ''
        while tmp[-1][-1] == '\\':
            self.__fidx += 1
            tmp.append(self.get_line()[0].strip())
        if len(tmp) > 1:
            line = ' '.join([x.rstrip('\\') for x in tmp])
        return line

    def process_line(self, line, ctxt=None):
        '''outputs a dictionary with keys match and matcher

        match is the match object
        matcher is the Match object which matched
        returns None for both if there is no match'''
        result = {
            'matcher': None,
            'match': None
        }
        context = ctxt or self.__ctxt
        for match in context: # get the first matching regexp
            mtch = match.match(line)
            if mtch:
                result['matcher'] = match
                result['match'] = mtch
                break
        return result



    def tokenize_file(self):
        '''process a file, return a list of tokenized blocks'''
        block = self.get_block()
        result = []
        while block:
            proced_block = self.process_block(block)
            result.append(self.tokenize_block(proced_block))
            block = self.get_block()
        return result



def generate_all(tok_file):
    result = []
    for token_block in tok_file:
        for token in token_block:
            rndr = token.render()
            if rndr: result.append(rndr)
    return 'from test import *\n' + '\n'.join(result)

if __name__ == '__main__':
    import sys
    a = Parser(file(sys.argv[1]))
    RootMatch = Match('','')
    mtcha = Match('name_recorddef',RECORD_DEF_NAME)
    mtcha.append(Match('mainview_recorddef',RECORD_DEF_MAIN_VIEW))
    mtcha.append(Match('tabview_recorddef', RECORD_DEF_TAB_VIEW))
    mtcha.append(Match('defaultview_recorddef', RECORD_DEF_DEF_VIEW))
    mtcha.append(Match('recname_recorddef', RECORD_DEF_RECNAME_VIEW))
    mtcha.append(Match('end_recorddef', RECORD_DEF_END))
    MatchPrinter().prnt(mtcha)
    a.add_match(mtcha)
    a.add_match(Match('short_param', PARAM_SHORT))
    mtchb = Match('long_param', PARAM_LONG)
    mtchb.append(Match('long_param_cont', PARAM_LONG_CONT))
    a.add_match(mtchb)
    blnk = Match('blank_line', BLANK_LINE, shared=True)
    a.add_match(blnk)
    for mtch in (mtcha, mtchb, blnk):
        RootMatch.append(mtch)
    TokenClass('name_recorddef',RECORD_DEF_TEMPLATE)
    TokenClass('mainview_recorddef',RECORD_DEF_MAINVIEW_TEMPLATE)
    TokenClass('tabview_recorddef',RECORD_DEF_TABULARVIEW_TEMPLATE)
    TokenClass('defaultview_recorddef',RECORD_DEF_DEFAULTVIEW_TEMPLATE)
    TokenClass('recname_recorddef',RECORD_DEF_RECNAMEVIEW_TEMPLATE)
    TokenClass('end_recorddef',RECORD_DEF_END_TEMPLATE)
    TokenClass('short_param',SHORT_PARAM_TEMPLATE)
    TokenClass('long_param',LONG_PARAM_TEMPLATE)
    TokenClass('long_param_cont',LONG_PARAM_CONT_TEMPLATE)
    TokenClass('blank_line','')

    b = a.tokenize_file()
    res = generate_all(b)

    file(sys.argv[2],'w').write(res)
__version__ = "$Revision$".split(":")[1][:-1].strip()
