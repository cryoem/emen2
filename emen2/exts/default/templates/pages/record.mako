<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="relmap" file="/pages/map"  /> 

<%block name="stylesheet_inline">
	${parent.stylesheet_inline()}
	#content {
		padding: 0px;
	}
	#rendered {
		padding: 10px;
	}
</%block>


## Additional alerts
<%block name="alert">
	${parent.alert()}
	<ul id="alert" class="alert nonlist precontent">
		% if rec.get('deleted'):
			<li class="notify error">Deleted Record</li>
		% endif

		% if 'publish' in rec.get('groups', []):
			<li class="notify">Record marked as published data</li>
		% endif

		% if 'authenticated' in rec.get('groups', []):
			<li class="notify">Any authenticated user can access this Record</li>
		% endif
	</ul>
</%block>


## Relationship Map
<%block name="precontent">
	<br />
	${parent.precontent()}
	<div id="map" class="precontent">
		${relmap.traverse(tree=parentmap, root=rec.name, recurse=3, recnames=recnames, mode='parents')}		
	</div>
</%block>

## Cached items
<%block name="javascript_inline">
	${parent.javascript_inline()}
	caches['record'][${jsonrpc.jsonutil.encode(rec.name)}] = ${jsonrpc.jsonutil.encode(rec)};
	caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};
	caches['displaynames'] = ${jsonrpc.jsonutil.encode(displaynames)};
</%block>

## Start map browser
<%block name="javascript_ready">
	${parent.javascript_ready()}
	$('#map .e2-map').RelationshipControl({'attach':true});
</%block>

${next.body()}
