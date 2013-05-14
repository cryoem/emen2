var ROOT = ${ctxt.root | n,jsonencode};
var VERSION = ${ctxt.version | n,jsonencode};

<%!
public = True
headers = {
    'Content-Type': 'application/javascript',
    'Cache-Control': 'max-age=86400'
}
%>
