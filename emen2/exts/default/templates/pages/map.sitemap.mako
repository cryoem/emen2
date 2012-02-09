<%! import jsonrpc.jsonutil  %>
<%inherit file="/page" />
<%namespace name="relmap" file="/pages/map"  /> 

<%block name="js_ready">
	$("#sitemap").BrowseControl({
		root: ${jsonrpc.jsonutil.encode(root)},
		controls: $('#sitemap'),
		show: true,
		embed: true,
	});
</%block>

<h1>Sitemap</h1>

<div id="sitemap"></div>