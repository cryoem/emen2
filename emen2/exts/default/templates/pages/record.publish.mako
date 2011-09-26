<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

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
		${buttons.spinner(false)}
		<input type="submit" value="Save" name="save">
	</div>
</h1>

<div id="publishmap">
${childmap}
</div>
