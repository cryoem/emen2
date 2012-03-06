<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 


## emen2.caches["children"] = ${jsonrpc.jsonutil.encode(children)};
## emen2.caches["collapsed"] = ${jsonrpc.jsonutil.encode(dict([(k, list(v)) for k,v in collapsed.items()]))};


<%block name="js_ready">
	${parent.js_ready()}
	$('#publishmap').MapControl({
		name: ${rec.name},
		attach: true,
		selected: function(e, self, p, c){
			e.preventDefault();
			console.log(e, self, p, c);
			var elems = $('[data-name='+c+']', self.element);
			elems.toggleClass('e2-browse-selected');
		}
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
