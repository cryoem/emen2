<%inherit file="/page" />
<%namespace name="table" file="/pages/table"  /> 

<%def name="head()">
	<% import jsonrpc.jsonutil %>
	<script type="text/javascript">
	//<![CDATA[
		$(document).ready(function() {
			$('#qc').QueryControl({
				q: ${jsonrpc.jsonutil.encode(q)}
			});
		});	
	//]]>
	</script>

	<style type="text/css">
		#content {
			width:auto !important;
		}
	</style>
</%def>

<div id="qc">
</div>

<p></p>

${table.table(q, qc=False)}
