<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="relmap" file="/pages/map"  /> 
<%import jsonrpc.jsonutil %>

## Additional alerts
<%def name="alert()">
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
</%def>


## Remove the #content padding; pad the inner div #rendered
<%def name="extrastyle()">
#content {
	padding:0px;
}
#rendered {
	padding:10px;
}
</%def>


## Relationship Map
<%def name="precontent()">
	<div id="map" class="precontent">
		${relmap.traverse(tree=parentmap, root=rec.name, recurse=3, recnames=recnames, mode='parents')}		
	</div>
</%def>


## Init script
<script type="text/javascript">
//<![CDATA[
	caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};
	caches['displaynames'] = ${jsonrpc.jsonutil.encode(displaynames)};
	$('#map .e2-map').RelationshipControl({'attach':true});
//]]>
</script>

${next.body()}
