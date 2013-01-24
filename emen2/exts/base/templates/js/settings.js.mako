<%!
public = True
headers = {
    'Content-Type': 'application/javascript',
    'Cache-Control': 'max-age=86400'
}

import emen2.db.datatypes
import jsonrpc.jsonutil
import operator

vtm = emen2.db.datatypes.VartypeManager()
properties={}
for prop in vtm.get_properties():
    p = vtm.get_property(prop)
    properties[prop] = [p.defaultunits, p.units]
%>

## Don't forget to disable escaping with | n
var ROOT = ${ctxt.root | n,jsonencode};
var VERSION = ${ctxt.version | n,jsonencode};
var valid_properties = ${properties | n,jsonencode};
var valid_vartypes = ${vtm.get_vartypes() | n,jsonencode};


