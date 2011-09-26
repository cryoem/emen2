<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="table" file="/pages/table"  /> 

<%block name="js_ready">
	${parent.js_ready}
	$('#qc').QueryControl({
		q: ${jsonrpc.jsonutil.encode(q)}
	});
</%block>

<div id="qc"></div>

<p></p>

${table.table(q, qc=False)}
