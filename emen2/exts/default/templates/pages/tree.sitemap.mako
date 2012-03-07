<%! import jsonrpc.jsonutil  %>
<%inherit file="/page" />

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