<%inherit file="/page" />
<%namespace name="map" file="/pages/map"  />
<%! import jsonrpc.jsonutil  %>

<%block name="js_ready">
	$("#sitemap").RelationshipControl({
		attach:true,
		sitemap:true,
		root: ${jsonrpc.jsonutil.encode(root)}
	});
</%block>

<div id="sitemap" class="e2l-clearfix">
${childmap}
</div>

