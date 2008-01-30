import g
from string import Template
from subsystems.macro import add_macro

def make_registry(name, bases, dict):
    cls = type(name, bases, dict)
    cls._registry = {}
    return cls

class VarTypeRegistry(object):
    __metaclass__ = make_registry
    @classmethod
    def get(cls, name):
        return cls._registry.get(name, (None, None))
    @classmethod
    def set(cls, name, template, to_python):
        cls._registry[name] = (Template(template), to_python)

class DynamicValue(object):
    def __init__(self, function):
        self.__function = function
    def __get__(self, *args):
        try:
            return self.__function(args[0])
        except TypeError:
            return self.__function

class FormField(object):
    def __init__(self, id, label, vartype, jscls='', value=None):
        self.__id = id
        self.__value = value
        self.__label = label
        self.__jscls = jscls
        self.vartype, to_python = VarTypeRegistry.get(vartype)
        self.to_python = to_python
    def make_field(self, append=''):
        self.__id = self.__id+str(append)
        if self.vartype == None: return '!!empty!!'
        return self.vartype.substitute(dict(id=self.__id, value=(self.__value or ''), label=self.__label, jscls=self.__jscls))
    field = DynamicValue(make_field)
    __str__ = make_field
    def process_dict(self, dict):
        raw = dict.get(self.__id, None)
        self.__value = self.to_python(raw)
        return (self.__id, self.__value)
    def get_value(self):
        result = self.__value
        if result == None:
            raise ValueError('No Value')
        return result
    value = property(get_value)

        
class Form(object):
    def __init__(self, fields):
        self.__fields = fields
    def __str__(self):
        return str.join('\n', [str(x) for x in self.__fields])
    def process_dict(self, dict):
        result = {}
        for i in self.__fields:
            result.update([i.process_dict(dict)])
        return result
            

def macroify(function):
    def inner(db, rec, parameters, **extra):
        args = parameters.split(' ')
        return function(*args)
    return inner

VarTypeRegistry.set('string', '<label for="$id">$label</label><input type="text" name="$id" value="$value" class="$jscls" />', str)
def string_field(id, label, value=''):
    field = FormField(id, label, 'string', value)
    return field
print add_macro('stringfield')(macroify(string_field))

VarTypeRegistry.set('integer', '<label for="$id">$label</label><input type="text" name="$id" value="$value" class="$jscls" />', str)
def integer_field(id, label, value=''):
    field = FormField(id, label, 'integer', value)
    return field
print add_macro('intfield')(macroify(integer_field))

VarTypeRegistry.set('text', '<label for="$id">$label</label><textarea name="$id">$value</textarea>', str)
def text_field(id, label, value=''):
    field = FormField(id, label, 'text', value)
    return field
print add_macro('textfield')(macroify(text_field))
