<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%import jsonrpc.jsonutil %>

## Additional alerts

<%def name="alert()">
	<ul id="alert" class="alert nonlist precontent">
	% if rec.get('deleted'):
		<li class="notify error">Deleted Record</li>
	% endif

	% if 'publish' in rec.get('groups', []):
		<li class="notify">Record marked as Published Data</li>
	% endif

	% if 'authenticated' in rec.get('groups', []):
		<li class="notify">Any authenticated user can access this Record</li>
	% endif
	</ul>
</%def>


<%def name="extrastyle()">
#content {
	padding:0px;
}
#rendered {
	padding:10px;
}
</%def>


## Init script

<script type="text/javascript">
//<![CDATA[
	caches['recnames'][${rec.name}] = ${jsonrpc.jsonutil.encode(renderedrecname)};
	caches['displaynames'] = ${jsonrpc.jsonutil.encode(displaynames)};
//]]>
</script>

${next.body()}
