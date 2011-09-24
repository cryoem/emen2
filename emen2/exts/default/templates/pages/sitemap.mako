<%inherit file="/page" />
<%namespace name="map" file="/pages/map"  />
<% 
import jsonrpc.jsonutil 
%>

<script type="text/javascript">
//<![CDATA[
	$(document).ready(function() {
		$("#sitemap").RelationshipControl({
			attach:true,
			sitemap:true,
			root: ${jsonrpc.jsonutil.encode(root)}
		});
	});	
//]]>
</script>

<div id="sitemap" class="e2l-clearfix">
${childmap}
</div>

