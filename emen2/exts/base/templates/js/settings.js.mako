<%!
public = True
headers = {
    'Content-Type': 'application/javascript',
    'Cache-Control': 'max-age=86400'
}

import emen2.db.properties
import emen2.db.vartypes
import jsonrpc.jsonutil
import operator

properties={}
for k,v in emen2.db.properties.Property.registered.items():
    v = v()
    properties[k] = [v.defaultunits, v.units]
%>

## These might need stronger escaping.
var ROOT = ${ctxt.root | n,jsonencode};
var VERSION = ${ctxt.version | n,jsonencode};
var valid_properties = ${properties | n,jsonencode};
var valid_vartypes = ${emen2.db.vartypes.Vartype.registered.keys() | n,jsonencode};


