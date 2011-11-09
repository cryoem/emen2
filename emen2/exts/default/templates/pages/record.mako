<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="css_inline">
	${parent.css_inline()}
	#content {
		width: auto;
		padding: 0px;
	}
	#rendered {
		padding: 10px;
	}
</%block>

## Relationship Map
<%block name="precontent">
	${parent.precontent()}
	<div class="e2-map-main">${parentmap}</div>
</%block>


## Cached items
<%block name="js_inline">
	${parent.js_inline()}
	${buttons.tocache(rec)}
	emen2.caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};
</%block>


## Start map browser
<%block name="js_ready">
	${parent.js_ready()}
	$('.e2-map').MapControl({'attach':true});
</%block>

${next.body()}
