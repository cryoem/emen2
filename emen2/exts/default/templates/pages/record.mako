<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

## Relationship Map
<%block name="precontent">
	${parent.precontent()}
	<div class="e2-map-main">${parentmap}</div>
</%block>


## Start map browser
<%block name="js_ready">
	${parent.js_ready()}
	${buttons.tocache(rec)}
	emen2.caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};
	$('.e2-map').MapControl({'attach':true});
</%block>

${next.body()}
