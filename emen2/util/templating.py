"""\
Interfaces:

TemplateLoader:
    a dictionary like object that takes a key and returns a template object
   
TemplateEngine:
    a object with these methods:
    templates = {}
    get_template(name)
    add_template(name, template)
    render_template(name, context)
        returns a string
"""

import mako.template
import mako.lookup
import jinja

class TemplateFactory(object):
   def __init__(self, default_engine_name, default_engine):
       self.__template_registry = {}
       self.register_template_engine(default_engine_name, default_engine)
       self.set_default_template_engine(default_engine_name)
       self.set_current_template_engine(default_engine_name)
       
   def render_template(self, name, context):
       template_engine = self.get_current_template_engine()
       return template_engine.render_template(name, context)
       
   def add_template(self, name, template_string): 
       self.__currentengine.add_template(name, template_string)
       
   def set_default_template_engine(self, engine_name):
       self.__defaultengine = self.__template_registry[engine_name]
       
   def get_default_template_engine(self):
       return self.__defaultengine
   
   def set_current_template_engine(self, engine_name):
       self.__currentengine = self.__template_registry[engine_name]
       
   def get_current_template_engine(self):
       return self.__currentengine
    
   def register_template_engine(self, engine_name, engine):
       self.__template_registry[engine_name] = engine
       
class AbstractTemplateLoader(object):
    '''template loaders are dictionary like objects'''
    templates = {}
    def __getitem__(self, name):
        return self.templates[name]
    def __setitem__(self, name, value):
        self.templates[name] = value

class JinjaTemplateLoader(AbstractTemplateLoader):
    env = jinja.Environment()
    def __setitem__(self, name, value):
        self.templates[name] = self.env.from_string(value)

class MakoTemplateLoader(mako.lookup.TemplateCollection, AbstractTemplateLoader):
    def __setitem__(self, name, value):
        self.templates[name] = mako.template.Template(value, lookup=self)
    def get_template(self, uri, relativeto=None):
        try:
            return self[uri]
        except KeyError:
            return 'No Template: %s' % uri
    
class AbstractTemplateEngine(object):
    '''Useless Example Implementation of a Template Engine'''
    templates = AbstractTemplateLoader()
    def get_template(self, name):
        return self.templates[name]
    def add_template(self, name, template_string):
        print self.templates
        self.templates[name] = template_string
    def render_template(self, name, context):
        return self.templates[name]

class StandardTemplateEngine(AbstractTemplateEngine):
    def render_template(self, name, context):
        return self.templates[name].render(**context)
        
class JinjaTemplateEngine(StandardTemplateEngine):
    templates = JinjaTemplateLoader()
    
class MakoTemplateEngine(StandardTemplateEngine):
    templates = MakoTemplateLoader()
