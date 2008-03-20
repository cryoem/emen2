from emen2.subsystems.formgenerator import Form, FormField, StringVar, TextVar, \
                                                                     IntVar, VarTypeRegistry, ImageVar, \
                                                                     ChoiceVar            
from emen2.subsystems.macro import add_macro
import g

def macroify(function):
    def inner(db, rec, parameters, **extra):
        args = parameters.split(' ')
        return function(*args)
    return inner

def string_field(id, label, value=''):
    field = FormField(id, label, StringVar(), value)
    return field
print add_macro('stringfield')(macroify(string_field))

def integer_field(id, label, value=''):
    field = FormField(id, label, IntVar(), value)
    return field
print add_macro('intfield')(macroify(integer_field))

def text_field(id, label, value=''):
    field = FormField(id, label, TextVar(), value)
    return field
print add_macro('textfield')(macroify(text_field))

def join(lis):
    return str.join('\n', lis.split('\t'))

def combined_string_field(id, label, value=''):
    field = [ FormField(id, label, StringVar(), value), FormField(id, label, StringVar(), value) ][0]
    return field
print add_macro('combinedstringfield')(macroify(string_field))

def choice_field(id, label, value='', choices=None):
    choices = choices or []
    field = FormField(id, label, ChoiceVar(choices=choices), value)
    return field
print add_macro('choicefield')(macroify(string_field))

def image_field(id, label, value=''):
    field = FormField(id, label, ImageVar(), value)
    return field
print add_macro('image')(macroify(integer_field))
print add_macro('binaryimage')(macroify(integer_field))

def formfromrecorddef(recorddef, db, order=None, override=None, init=None):
    """
    Generate a form given a recorddef.
    
    @param recorddef: The recorddef for which a form needs to be generated
    @type recorddef: Database.RecordDef
    @param db: a Database instance
    @type db: Database.Database
    @param order: The order of the fields in the form, defaults to alphabetical by key 
    @type order: list
    @param override: Keys to override with a custom field
    @type override: dict
    """
    fields = []
    override = override or {}
    init = init or {}
    
    for field in (order or recorddef.params.keys()):
        pd = db.getparamdef(field)
        tmp = FormField(field, pd.desc_short+':', VarTypeRegistry.get(pd.vartype), value=str(recorddef.params[field] or ''))
        tmp = override.get(field, tmp)
        fields.append(tmp)
    
    result = Form(fields)
    result.bind_value(**init)
    return result

def comb_field(id, label, value=None):
    field = FormField(id, label, ChoiceVar(value))
    return field
print add_macro('combinedstringfield')(macroify(string_field))
