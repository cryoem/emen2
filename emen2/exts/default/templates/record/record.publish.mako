<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 


## emen2.caches["children"] = ${jsonrpc.jsonutil.encode(children)};
## emen2.caches["collapsed"] = ${jsonrpc.jsonutil.encode(dict([(k, list(v)) for k,v in collapsed.items()]))};

<%block name="js_inline">

	var published = ${jsonrpc.jsonutil.encode(published)};

	function pub_add(name) {
		emen2.util.set_add(name, published);
		var elems = $('[data-name='+name+']', self.element);
		elems.addClass('e2-browse-selected');		
		pub_count_update();		
	}
	
	function pub_remove(name) {
		emen2.util.set_remove(name, published);
		var elems = $('[data-name='+name+']', self.element);
		elems.removeClass('e2-browse-selected');
		pub_count_update();		
	}
	
	function pub_count_update() {
		$("#pub_count").html(published.length);
	}

	function pub_select(e, self, elem) {
		e.preventDefault();
		var elem = $(elem);
		var elem_p = elem.parent();
		var name = elem_p.attr('data-name');
		var state = elem_p.hasClass('e2-browse-selected');
		emen2.db('getchildren', {names:name, recurse:-1}, function(children) {
			children.push(name);
			for (var i=0; i < children.length; i++) {
				if (state) {
					pub_remove(children[i]);
				} else {
					pub_add(children[i]);
				}
			}
		});
	}
	
	
	
</%block>


<%block name="js_ready">
	${parent.js_ready()}
	$('#publishmap').MapControl({
		name: ${rec.name},
		attach: true,
		selected: pub_select
	});
</%block>


<form method="post" action="">
<h1>
	<span id="pub_count">${len(published)}</span> published records
	<div class="e2l-controls" id="ext_save">
		${buttons.spinner(false)}
		<button type="submit">${buttons.spinner(False)} Save</button>
	</div>
</h1>

<div id="publishmap">
${childmap}
</div>
</form>