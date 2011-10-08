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
for prop in vtm.getproperties():
	p = vtm.getproperty(prop)
	properties[prop] = [p.defaultunits, p.units]
%>

var EMEN2WEBROOT=${jsonrpc.jsonutil.encode(EMEN2WEBROOT)};
var VERSION=${jsonrpc.jsonutil.encode(VERSION)};

var valid_properties=${jsonrpc.jsonutil.encode(properties)};
var valid_vartypes=${jsonrpc.jsonutil.encode(vtm.getvartypes())};

var reverse_uri='${ctxt.reverse('ReverseURI_alt')}';


