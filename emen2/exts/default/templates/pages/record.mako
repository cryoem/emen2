<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="css_inline">
	${parent.css_inline()}
</%block>


## Relationship Map
<%block name="precontent">
	${parent.precontent()}
	${parentmap}		
</%block>


## Cached items
<%block name="js_inline">
	${parent.js_inline()}
	${buttons.tocache(rec)}
	caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};
	caches['displaynames'] = ${jsonrpc.jsonutil.encode(displaynames)};
</%block>


## Start map browser
<%block name="js_ready">
	${parent.js_ready()}
	$('.e2-map').MapControl({'attach':true});
</%block>

${next.body()}
