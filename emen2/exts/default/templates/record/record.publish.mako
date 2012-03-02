<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<% 
import jsonrpc.jsonutil 
%>



<%block name="js_ready">
	${parent.js_ready()}
	emen2.caches["children"] = ${jsonrpc.jsonutil.encode(children)};
	emen2.caches["collapsed"] = ${jsonrpc.jsonutil.encode(dict([(k, list(v)) for k,v in collapsed.items()]))};

	$('#publishmap').MapSelect({
		name: ${rec.name},
		status: ${jsonrpc.jsonutil.encode(status)},
		ext_save: '#ext_save'
	});
</%block>


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