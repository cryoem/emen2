<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="table" file="/pages/table"  /> 

<%block name="javascript_ready">
	${parent.javascript_ready}
	$('#qc').QueryControl({
		q: ${jsonrpc.jsonutil.encode(q)}
	});
</%block>

<div id="qc"></div>

<p></p>

${table.table(q, qc=False)}
