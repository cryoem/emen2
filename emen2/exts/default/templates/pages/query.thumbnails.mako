<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />

<%
# Would be nice to have a [vartype=binary] selector
q = DB.query([['creationtime', '>=', 'bdo:2012']], keytype='binary')
%>

${q}


## % for rec, bdos in c.items():
##    
##    <h1><a href="${EMEN2WEBROOT}/record/${rec}/">${recnames.get(rec, rec)}</a></h1>
##    <ul>
##    % for bdo in bdos:
##        <li>${bdo.filename}</li>
##    % endfor
##    </ul>
## % endfor