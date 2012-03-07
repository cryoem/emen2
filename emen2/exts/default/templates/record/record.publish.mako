<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="js_ready">
	${parent.js_ready()}
	$('#publishmap').TreeSelectControl({
		attach: true,
		display_count: '#publish_count'
	});
	// $('#publishmap').TreeSelectControl('add', ${jsonrpc.jsonutil.encode(published)});
</%block>


<form method="post" action="">
<h1>
	<span id="publish_count">${len(published)}</span> records selected
	<div class="e2l-controls" id="ext_save">
		${buttons.spinner(false)}
		<button type="submit">${buttons.spinner(False)} Save</button>
	</div>
</h1>

<div id="publishmap">
	${childmap}
</div>

</form>