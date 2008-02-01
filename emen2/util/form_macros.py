import g
from subsystems.macro import add_macro
from subsystems.formgenerator import Form, FormField, VarTypeRegistry            

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

def join(lis):
    return str.join('\n', lis.split('\t'))
VarTypeRegistry.set('combined_string', '<label for="$id">$label</label><input type="text" name="$id" value="$value" class="$jscls" /><input type="text" name="$id" value="$value" class="$jscls" />', join)
def combined_string_field(id, label, value=''):
    field = FormField(id, label, 'combined_string', value)
    return field
print add_macro('combinedstringfield')(macroify(string_field))

def formfromrecorddef(recorddef, db):
    fields = []
    for field in recorddef.params.keys():
        pd = db.getparamdef(field)
        tmp = FormField(field, pd.desc_short+':', pd.vartype, value=str(recorddef.params[field] or ''))
        fields.append(tmp)
    return Form(g.debug.note_var(fields))
