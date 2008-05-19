from emen2.subsystems.formgenerator import Form, FormField, StringVar, TextVar, \
                                                                     IntVar, VarTypeRegistry, ImageVar, \
                                                                     ChoiceVar            
from emen2.subsystems.macro import add_macro
from functools import partial

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

def macroify(function):
    def inner(db, rec, parameters, **extra):
        args = parameters.split(' ')
        return function(*args)
    return inner

def string_field(id, label, value=''):
    field = FormField(id, label, StringVar, value)
    return field
add_macro('stringfield')(macroify(string_field))

def integer_field(id, label, value=''):
    field = FormField(id, label, IntVar( value))
    return field
add_macro('intfield')(macroify(integer_field))

def text_field(id, label, value=''):
    field = FormField(id, label, TextVar, value)
    return field
add_macro('textfield')(macroify(text_field))

def join(lis):
    return str.join('\n', lis.split('\t'))

def combined_string_field(id, label, value=''):
    field = [ FormField(id, label, StringVar, value), FormField(id, label, StringVar, value) ][0]
    return field
add_macro('combinedstringfield')(macroify(string_field))

def choice_field(id, label, value='', choices=None):
    choices = choices or []
    field = FormField(id, label, ChoiceVar, value)
    return field
add_macro('choicefield')(macroify(string_field))

def image_field(id, label, value=''):
    field = FormField(id, label, ImageVar, value)
    return field
add_macro('image')(macroify(integer_field))
add_macro('binaryimage')(macroify(integer_field))

#@g.debug.debug_func
def paramdeftofield(param, rec, db, ctxid, host=None):
    paramargs = {}
    if param:
        pd = db.getparamdef(param)
        if pd.choices and pd.vartype == 'choice':
            paramargs['choices'] = pd.choices
        
        if pd.vartype.endswith('image'):
            paramargs['db'] = db
            paramargs['ctxid'] = ctxid
            paramargs['host'] = host
            if hasattr(rec, 'recid'):
                paramargs['recid'] = rec.recid or 0
            else:
                paramargs['recid'] = 0
        
        return FormField(param, pd.desc_short + ':', VarTypeRegistry.get(pd.vartype), value=rec.get(param) or '', args=paramargs)

def formfromrecorddef(recorddef, db, ctxid=None, host=None, order=None, override=None, init=None, rec=None, **kwargs):
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
        tmp = paramdeftofield(field, rec or recorddef.params, db, ctxid, host=None)
        tmp = override.get(field, tmp)
        fields.append(tmp)
    
    result = Form(fields)
    result.bind_value(**init)
    return result

def comb_field(id, label, value=None):
    field = FormField(id, label, ChoiceVar)
    return field
add_macro('combinedstringfield')(macroify(string_field))

def procform(recdef, argdict, db, ctxid, override=None, host=None):
    override = override or {}
    getrecorddef = partial(db.getrecorddef, ctxid=ctxid, host=host)
    rec = db.newrecord(recdef, ctxid, host=host)
    form = formfromrecorddef(getrecorddef(recdef), db)
    res = form.process_dict(argdict)
    if rec:
        overidden = set(override.keys()) & set(res.keys())
        for key in overidden:
            res[key] = override[key] 
    rec.update(res) 
    id = db.putrecord(rec, ctxid, host=host)
    return id 
