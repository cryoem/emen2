<%inherit file="/page" />

<% 
import jsonrpc.jsonutil 
%>


<script type="text/javascript">
//<![CDATA[

	$(document).ready(function() {
		
		caches["children"] = ${jsonrpc.jsonutil.encode(children)};
		caches["collapsed"] = ${jsonrpc.jsonutil.encode(dict([(k, list(v)) for k,v in collapsed.items()]))};

		$('#publishmap').MapSelect({
			name: ${rec.name},
			status: ${jsonrpc.jsonutil.encode(status)},
			ext_save: '#ext_save'
		});
	});


//]]>
</script>


<h1>
	Published Records
	<div class="e2l-controls" id="ext_save">
		<img class="e2l-spinner hide" src="${EMEN2WEBROOT}/static/images/spinner.gif" alt="Loading" />
		<input type="submit" value="Save" name="save">
	</div>
</h1>

<div id="publishmap">
${childmap}
</div>
