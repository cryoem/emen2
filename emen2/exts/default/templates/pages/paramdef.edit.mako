<%! import jsonrpc.jsonutil %>
<%inherit file="/pages/paramdef" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<form method="post" action="${ctxt.reverse('ParamDef/edit', name=paramdef.name)}">

<h1>
	${title}
	<ul class="e2l-actions">
		<li><input type="submit" value="Save" /></li>
	</ul>
</h1>


${self.paramdef_edit(paramdef, edit=edit, new=new)}

<%buttons:singlepage label='Relationships'>
	<div id="e2-relationships" data-name="${paramdef.name}" data-keytype="${paramdef.keytype}"></div>
</%buttons:singlepage>

</form>