<%! import jsonrpc.jsonutil %>
<%inherit file="/pages/paramdef" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<h1>
	${title}

	<ul class="e2l-actions">
		<li><a class="e2-button" href="${EMEN2WEBROOT}/query/${paramdef.name}.!None./">${buttons.image('query.png', 'Query')} Query</a></li>

		% if editable:
			<li><a class="e2-button" href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/edit/">${buttons.image('edit.png', 'Edit')} Edit</a></li>
		% endif

		% if create:
			<li><a class="e2-button" href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="New" /> New</a></li>
		% endif
	</ul>
</h1>


${self.paramdef_edit(paramdef, edit=edit, new=new)}

<%buttons:singlepage label='Relationships'>
	<div id="e2-relationships" data-name="${paramdef.name}" data-keytype="${paramdef.keytype}"></div>
</%buttons:singlepage>
