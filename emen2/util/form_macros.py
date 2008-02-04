import g
from subsystems.macro import add_macro
from subsystems.formgenerator import Form, FormField, StringVar, TextVar, IntVar, VarTypeRegistry            

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
    field = FormField(id, label, StringVar(), value)
    return field
print add_macro('combinedstringfield')(macroify(string_field))

def formfromrecorddef(recorddef, db):
    fields = []
    for field in recorddef.params.keys():
        pd = db.getparamdef(field)
        tmp = FormField(field, pd.desc_short+':', VarTypeRegistry.get(pd.vartype), value=str(recorddef.params[field] or ''))
        fields.append(tmp)
    return Form(g.debug.note_var(fields))
