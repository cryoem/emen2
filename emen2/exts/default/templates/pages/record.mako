<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="relmap" file="/pages/map"  /> 

<%block name="css_inline">
	${parent.css_inline()}
	#content {
		padding: 0px;
	}
	#rendered {
		padding: 10px;
	}
</%block>


## Relationship Map
<%block name="precontent">
	<br />
	${parent.precontent()}
	<div id="map" class="e2l-precontent">
		${relmap.traverse(tree=parentmap, root=rec.name, recurse=3, recnames=recnames, mode='parents')}		
	</div>
</%block>

## Cached items
<%block name="js_inline">
	${parent.js_inline()}
	caches['record'][${jsonrpc.jsonutil.encode(rec.name)}] = ${jsonrpc.jsonutil.encode(rec)};
	caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};
	caches['displaynames'] = ${jsonrpc.jsonutil.encode(displaynames)};
</%block>

## Start map browser
<%block name="js_ready">
	${parent.js_ready()}
	$('#map .e2-map').RelationshipControl({'attach':true});
</%block>

${next.body()}
